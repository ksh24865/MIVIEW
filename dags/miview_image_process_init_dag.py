from datetime import datetime, timedelta, date
import json
import boto3
import miview_db
import google_drive_funcs as gdf
import aws_funcs as af
import miview
import dcm2img
import os
from deep.predict import run_script
from airflow import DAG
from airflow.operators.python import PythonOperator


default_args = {
    "owner": "miview",
    "start_date": datetime.today() - timedelta(hours=25),
}

# miview_token_refresh

# def main():
#     user_id = 12
    
    
#     service = gdf.get_service(user_id)
#     print("service:",service)
#     len_of_files = _download_images(service,user_id)
#     _convert_image(user_id,len_of_files)
#     _segmentation_img(user_id,len_of_files)
#     _create_folders(user_id,len_of_files)

# def _get_service(**context):
#     print("START _get_service ")
#     params = context["params"]["conf"]
#     user_id = params["user_id"]
#     service = gdf.get_service(user_id)
#     ret = {"user_id": user_id, "service": service}
#     print("END _get_service ")
#     return ret


def _download_image(**context):
    params = context["params"]["conf"]
    user_id = params["user_id"]
    service = gdf.get_service(user_id)
    print("START _download_image ")
    # xcom_data = context["ti"].xcom_pull(task_ids="miview_get_service")
    # user_id = xcom_data.get("user_id")
    # service = xcom_data.get("service")
    folder_id = miview_db.get_user_folder_id(user_id)
    print("### 폴더 내 파일 출력 ###")
    get_file_in_folder_query = gdf.queries["get_file_in_folder"].format(folder_id=folder_id)
    items = gdf.get_file_list(service, get_file_in_folder_query, 100)
    gdf.print_items(items)
    len_of_files = gdf.download_items(service,items,user_id)

    xcom_data = {"user_id":user_id,"len_of_files":len_of_files}
    return xcom_data
    

def _convert_image(**context):
    print("START _convert_image ")
    xcom_data = context["ti"].xcom_pull(task_ids="miview_download_image")
    user_id = xcom_data.get("user_id")
    len_of_files = xcom_data.get("len_of_files")
    img_count = miview_db.get_user_img_count(user_id)
    for file_id in range(img_count,img_count+len_of_files):
        dcm2img.run_script(f"miview/user_{user_id}/origin/{file_id}.dcm",f"miview/user_{user_id}/converted/{file_id}.png")
    print(os.listdir(f"miview/user_{user_id}"))
    print(os.listdir(f"miview/user_{user_id}/origin"))
    os.listdir(f"miview/user_{user_id}/converted")
    xcom_data.update({"img_count":img_count})
    return xcom_data

def _segmentation_img(**context):
    xcom_data = context["ti"].xcom_pull(task_ids="miview_convert_image")
    user_id = xcom_data.get("user_id")
    # print(os.listdir(f"."))
    # img_count = miview_db.get_user_img_count(user_id)
    run_script("dags/body.pth",f"miview/user_{user_id}/converted",f"miview/user_{user_id}")
    # for file_id in range(img_count,img_count+len_of_files):
    #     miview.segmentation_img(f"miview/user_{user_id}/{file_id}.dcm",
    #         f"miview/user_{user_id}/converted/{file_id}.png"
    #         )

def _upload_to_google_drive(**context):
    
    xcom_data = context["ti"].xcom_pull(task_ids="miview_convert_image")
    user_id = xcom_data.get("user_id")
    service = gdf.get_service(user_id)#service = xcom_data.get("service")
    len_of_files = xcom_data.get("len_of_files")
    img_count = xcom_data.get("img_count")
    
    converted_folder_id = gdf.create_folder(service, "miview_converted")
    masked_folder_id = gdf.create_folder(service, "miview_masked")
    combined_folder_id = gdf.create_folder(service, "miview_combined")        
    
    
    gdf.upload_all_items(service,"converted",img_count,len_of_files,user_id,converted_folder_id)
    gdf.upload_all_items(service,"segmentation/combine",img_count,len_of_files,user_id,masked_folder_id)
    gdf.upload_all_items(service,"segmentation/mask",img_count,len_of_files,user_id,combined_folder_id)

def _upload_to_aws_s3(**context):
    bucket_name = af.bucket_name
    xcom_data = context["ti"].xcom_pull(task_ids="miview_convert_image")
    user_id = xcom_data.get("user_id")
    len_of_files = xcom_data.get("len_of_files")
    img_count = xcom_data.get("img_count")
    af.upload_all_files_to_s3(bucket_name,"converted","converted",img_count,len_of_files,user_id)
    af.upload_all_files_to_s3(bucket_name,"segmentation/combine","combine",img_count,len_of_files,user_id)
    af.upload_all_files_to_s3(bucket_name,"segmentation/mask","mask",img_count,len_of_files,user_id)

def _update_db(**context):
    xcom_data = context["ti"].xcom_pull(task_ids="miview_convert_image")
    user_id = xcom_data.get("user_id")
    len_of_files = xcom_data.get("len_of_files")
    miview_db.update_user_info(user_id,len_of_files)
    



# main()

with DAG(
    dag_id="miview_image_process_init",
    description="miview_image_process_init",
    default_args=default_args,
    catchup=False,
    schedule_interval=None,
    max_active_runs=5,
) as dag:
    params = {"conf": "{{ dag_run.conf['conf'] }}"}

    # miview_get_service = PythonOperator(
    #     task_id="miview_get_service",
    #     python_callable=_get_service,
    #     params=params,
    # )

    miview_download_image = PythonOperator(
        task_id="miview_download_image",
        python_callable=_download_image,
        params=params,
    )

    miview_convert_image = PythonOperator(
        task_id="miview_convert_image",
        python_callable=_convert_image,
        params=params,
    )

    miview_segmentation_img = PythonOperator(
        task_id="miview_segmentation_img",
        python_callable=_segmentation_img,
        params=params,
    )

    miview_upload_to_google_drive = PythonOperator(
        task_id="miview_upload_to_google_drive",
        python_callable=_upload_to_google_drive,
        params=params,
    )

    miview_upload_to_aws_s3 = PythonOperator(
        task_id="miview_upload_to_aws_s3",
        python_callable=_upload_to_aws_s3,
        params=params,
    )

    miview_update_db = PythonOperator(
        task_id="miview_update_db",
        python_callable=_update_db,
        params=params,
    )

    
    # miview_get_service >>
( miview_download_image >> miview_convert_image >>
    miview_segmentation_img >> (miview_upload_to_google_drive, miview_upload_to_aws_s3) >> miview_update_db)