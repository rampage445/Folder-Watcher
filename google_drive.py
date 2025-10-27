from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import mimetypes
import time

def create_nested_folders(path, parent_id):
    creds = Credentials(
        token=os.environ['ACCESS_TOKEN'],
        refresh_token=os.environ['REFRESH_TOKEN'],
        client_id=os.environ['CLIENT_ID'],
        client_secret=os.environ['CLIENT_SECRET'],
        token_uri='https://oauth2.googleapis.com/token'
    )
    drive_service = build('drive', 'v3', credentials=creds)

    folder_id = parent_id
    for folder_name in path.split('/'):
        query = (
            f"'{folder_id}' in parents and name = '{folder_name}' and "
            "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        response = drive_service.files().list(q=query, fields='files(id, name)').execute()
        files = response.get('files', [])
        if files:
            folder_id = files[0]['id']
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [folder_id]
            }
            folder = drive_service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
    return folder_id


def upload_file_to_drive(folder_id, file_path):
    creds = Credentials(
        token=os.environ['ACCESS_TOKEN'],
        refresh_token=os.environ['REFRESH_TOKEN'],
        client_id=os.environ['CLIENT_ID'],
        client_secret=os.environ['CLIENT_SECRET'],
        token_uri='https://oauth2.googleapis.com/token'
    )
    drive_service = build('drive', 'v3', credentials=creds)
    filename = os.path.basename(file_path)
    mime, _ = mimetypes.guess_type(file_path)
    mime = mime or 'application/octet-stream'
    file_metadata = {'name': filename, 'parents': [folder_id]}
    file_size = os.path.getsize(file_path)
    if file_size > 1 * 1024 * 1024 * 1024: # File size > 1 GB
        media = MediaFileUpload(file_path, mimetype=mime, resumable=True, chunksize=10*1024*1024)
    else:
        media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
    request = drive_service.files().create(body=file_metadata, media_body=media, fields='id')
    response = None
    retry = 0
    while response is None:
        try:
            status, response = request.next_chunk()
        except Exception as e:
            retry += 1
            time.sleep(2 ** retry)
            if retry > 5:
                raise RuntimeError(f"Upload failed after 5 retries: {file_path}")
    return response.get('id')



def rename_file_on_drive(file_id, new_name):
    creds = Credentials(
        token=os.environ['ACCESS_TOKEN'],
        refresh_token=os.environ['REFRESH_TOKEN'],
        client_id=os.environ['CLIENT_ID'],
        client_secret=os.environ['CLIENT_SECRET'],
        token_uri='https://oauth2.googleapis.com/token'
    )
    drive_service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': new_name}
    updated_file = drive_service.files().update(fileId=file_id, body=file_metadata).execute()
    return updated_file.get('id')

def delete_file_from_drive(file_id):
    creds = Credentials(
        token=os.environ['ACCESS_TOKEN'],
        refresh_token=os.environ['REFRESH_TOKEN'],
        client_id=os.environ['CLIENT_ID'],
        client_secret=os.environ['CLIENT_SECRET'],
        token_uri='https://oauth2.googleapis.com/token'
    )
    drive_service = build('drive', 'v3', credentials=creds)
    drive_service.files().delete(fileId=file_id).execute()

