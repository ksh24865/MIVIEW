from __future__ import print_function
import pickle
import os.path
import io
from botocore import retries
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import copy
import aws_funcs as af
import os_funcs as of

# 폴더: application/vnd.google-apps.folder 

# If modifying these scopes, delete the file token.pickle.
bucket_name = "miview-data"
SCOPES = ['https://www.googleapis.com/auth/drive']
queries = {
    "get_folder" : "'{parents}' in parents and mimeType='application/vnd.google-apps.folder'",
    "get_file_in_folder" : "'{folder_id}' in parents",
    "get_file_by_name" : "name = '{file_name}'"

}

# def get_service(user_id):
#     creds = None
#     # The file token.json stores the user's access and refresh tokens, and is
#     # created automatically when the authorization flow completes for the first
#     # time.

#     if os.path.exists(f'{user_id}_token.json'):
#         creds = Credentials.from_authorized_user_file(f'{user_id}_token.json', SCOPES)
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)
#             # flow.redirect_uri = 'https://miview-pubilic.s3.ap-northeast-2.amazonaws.com/test_img.png'
#             # authorization_url, state = flow.authorization_url(
#             # # Enable offline access so that you can refresh an access token without
#             # # re-prompting the user for permission. Recommended for web server apps.
#             # access_type='offline',
#             # # Enable incremental authorization. Recommended as a best practice.
#             # include_granted_scopes='true')
#             # print("authorization_url:",authorization_url)
#             creds = flow.run_local_server(port=8080)
#             creds.refresh(Request())
#         # Save the credentials for the next run
#         with open(f'{user_id}_token.json', 'w') as token:
#             json_creds = creds.to_json()
#             token.write(json_creds)
#             af.upload_file_s3("miview-data", f"user_{user_id}/token.json", json_creds)


#     service = build('drive', 'v3', credentials=creds)
#     return service

def get_service(user_id):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token = af.load_json_data_from_s3(bucket_name, f"user_{user_id}/token.json")
    print(f"before:{token}")
    creds = Credentials.from_authorized_user_info(token, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # flow.redirect_uri = 'https://miview-pubilic.s3.ap-northeast-2.amazonaws.com/test_img.png'
            # authorization_url, state = flow.authorization_url(
            # # Enable offline access so that you can refresh an access token without
            # # re-prompting the user for permission. Recommended for web server apps.
            # access_type='offline',
            # # Enable incremental authorization. Recommended as a best practice.
            # include_granted_scopes='true')
            # print("authorization_url:",authorization_url)
            creds = flow.run_local_server(port=8080)
            # creds.refresh(Request())
        # Save the credentials for the next run
        
        json_creds = creds.to_json()
        token.write(json_creds)
        af.upload_file_s3("miview-data", f"user_{user_id}/token.json", json_creds)
    service = build('drive', 'v3', credentials=creds)
    return service

# def get_service(user_id):
#     creds = None
#     token = af.load_json_data_from_s3(bucket_name, f"user_{user_id}/token.json")
#     creds = Credentials.from_authorized_user_info(token, SCOPES)
#     service = build('drive', 'v3', credentials=creds)
#     return service

def refresh_token(user_id):
    token = af.load_json_data_from_s3(bucket_name, f"user_{user_id}/token.json")
    print(f"before:{token}\n{type(token)}")
    creds = Credentials.from_authorized_user_info(token, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())        
        # json_creds = creds.to_json()
        creds_json = {'token': creds.token,
          'refresh_token': creds.refresh_token,
          'token_uri': creds.token_uri,
          'client_id': creds.client_id,
          'client_secret': creds.client_secret,
          'scopes': creds.scopes}
        af.upload_json_data_to_s3("miview-data", f"user_{user_id}/token.json", creds_json)
        print(f"after:{creds_json}")

def get_id_from_items(items,idx):
    item = items[idx]
    item_id = item['id']
    return item_id

def get_file_list(service,query,page_size):
    results = service.files().list(
        q=query, pageSize=page_size, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items
def print_items(items):
    if not items:
        print('No files found.')
    else:
        print('Files:') 
        for item_num,item in enumerate(items):          
            print(f"item_num:{item_num} filename: {item['name']}, file_ID: {item['id']}")
def download_items(service,items,user_id):
    # 실제론 google drive 에서 S3로 다운로드

    for item_num,item in enumerate(items): 
        ext = item['name'].split(".")[-1]
        file_id = item['id']
        request = service.files().get_media(fileId=file_id)
        # print(os.path.realpath(__file__))
        # print(os.path.abspath(__file__))
        of.createDirectory(f"miview/user_{user_id}/origin")
        
        fh = io.FileIO(f"miview/user_{user_id}/origin/{item_num}.{ext}", 'w')        
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print ("Download %d%%." % int(status.progress() * 100))                

    return len(items)

def processing_img():
    print("TODO, processing_img")

def upload_items(service,file,ext,file_num,parents_id):
    # 실제론 S3의 mivew/user_id/ 에서 google drive로 업로드    
    file_metadata = {'name' : f"processed_{file_num}", 'parents' : [parents_id]}    
    ext = ext.lower()
    if ext == "jpg":
        img_type = "jpeg"
    elif ext == "png":
        img_type = "png"
    media = MediaIoBaseUpload(file, mimetype = f'image/{img_type}', resumable = True)
    file = service.files().create(body = file_metadata, media_body=media, fields='id').execute()

def upload_all_items(service, path, start_file_id, len_of_files, user_id, dest_id):
    # 실제론 S3의 mivew/user_id/ 에서 google drive로 업로드    
    for file_id in range(start_file_id,start_file_id+len_of_files):
        file_metadata = {'name' : f"processed_{file_id}", 'parents' : [dest_id]}    
        file = open(f"miview/user_{user_id}/{path}/{file_id}.png", 'rb')
        media = MediaIoBaseUpload(file, mimetype = f'image/png', resumable = True)
        service.files().create(body = file_metadata, media_body=media, fields='id').execute()

def do_create_folder(service,name):
    
    file_metadata = {
    'name': name,
    'mimeType': 'application/vnd.google-apps.folder'
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file.get('id')

def create_folder(service, name):
    get_file_by_name_query = queries['get_file_by_name'].format(file_name = name)
    dest_folder = get_file_list(service,get_file_by_name_query,1)
    if not dest_folder:
        dest_id = do_create_folder(service,name)
    else:
        dest_id = dest_folder[0]['id']
    return dest_id