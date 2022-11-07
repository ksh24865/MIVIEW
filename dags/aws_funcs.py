import json
import logging

import boto3
import io
bucket_name = "miview-data"

s3_client = boto3.client(
        's3',
        aws_access_key_id="",
        aws_secret_access_key=""
    )


def load_data_from_s3(bucket, file_name):
    obj = s3_client.get_object(Bucket=bucket, Key=file_name)
    body = io.BytesIO(obj["Body"].read())
    return body


def load_json_data_from_s3(bucket, file_name):
    obj = s3_client.get_object(Bucket=bucket, Key=file_name)    
    str_obj = str(obj["Body"].read(),"UTF-8")
    data = json.loads(str_obj)
    return data


def upload_json_data_to_s3(bucket, file_name, file):
    encode_file = bytes(json.dumps(file).encode("UTF-8"))
    s3_client.put_object(Bucket=bucket, Key=file_name, Body=encode_file)


def upload_file_to_s3(bucket, file_name, file):
    try:
        s3_client.put_object(Bucket=bucket, Key=file_name, Body=file)
        return True
    except:
        logging.warning("Failee to upload")
        return False


def upload_all_files_to_s3(bucket, path, file_name, start_file_id, len_of_files, user_id, ext = "png"):
    
    for file_id in range(start_file_id,start_file_id+len_of_files):
        s3_client.put_object(
            Body=open(f"miview/user_{user_id}/{path}/{file_id}.{ext}", 'rb'),
            Bucket=bucket,
            Key=f'user_{user_id}/{file_name}/{file_id}.png',
            ACL='public-read',
        )
    