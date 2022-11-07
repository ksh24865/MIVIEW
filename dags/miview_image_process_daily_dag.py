# from datetime import datetime, timedelta
# import json
# import boto3
# import miview_db
# import google_drive_funcs as gdf

# from airflow import DAG
# from airflow.operators.python import PythonOperator

# def _refresh_google_drive_token(**kwargs):
#     engine = miview_db.conn("miview")
#     users = engine.execute("select id from user;")
#     for user_id in users:
#         user_id = user_id[0]
#         print(user_id)
#         gdf.refresh_token(user_id)

# default_args = {
#     "owner": "miview",
#     "start_date": datetime.today() - timedelta(hours=25),
# }
# with DAG(
#     dag_id="miview_token_refresh_dag",
#     description="refresh_google_drive_token",
#     default_args=default_args,
#     catchup=False,
#     schedule_interval="0 * * * *",
#     max_active_runs=1,
# ) as dag:
#     params = {"conf": "{{ dag_run.conf['conf'] }}"}

#     miview_token_refresh = PythonOperator(
#         task_id="miview_token_refresh",
#         python_callable=_refresh_google_drive_token,
#         params=params,
#     )
# miview_token_refresh

