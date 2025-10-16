import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"] 

current_folder = './utilities'

SERVICE_ACCOUNT_FILE = os.path.join(current_folder, 'service_account_key.json') 

FOLDER_ID = '0APJmM8bO6kV5Uk9PVA'

def get_drive_service():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=creds)
        print("Auth on gdrive was successful.")
        return service
        
    except FileNotFoundError:
        print(f"Eroare: The file containing service key was not found at: {SERVICE_ACCOUNT_FILE}.")
        return None
    except Exception as e:
        print(f"An auth error occured: {e}")
        return None

def save_file_in_cloud(file_pth):
    print(f"Saving file {file_pth} in gdrive...")
    service = get_drive_service()
    if not service: return
    try:
        fname = os.path.basename(file_pth)
        file_metadata = {'name': fname,
                         'parents': [FOLDER_ID]}
        
        media = MediaFileUpload(file_pth, mimetype='application/octet-stream') 
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        print(f"File with ID-ul: {file.get('id')} was successfully uploaded.")
    except HttpError as error:
        print(f"An error occured: {error}")
    finally:
        if os.path.exists(file_pth):
            os.remove(file_pth)
            print(f"File '{file_pth}' has been removed from TMP folder.")
        else:
            print(f"File '{file_pth}' does not exist in local storage.")

def search_file_in_cloud(file_name):
    print("Searching for law reference in gdrive...")
    service = get_drive_service()
    if not service: return None
    fname = os.path.basename(file_name)
    try:
        query = f"name = '{fname}' and '{FOLDER_ID}' in parents"
        results = (
            service.files()
            .list(q=query, spaces="drive", fields="nextPageToken, files(id, name, mimeType)", includeItemsFromAllDrives=True, supportsAllDrives=True)
            .execute()
        )
        items = results.get("files", [])
        if not items:
            print(f"No file found with name '{fname}'.")
            return None
        file_info = items[0]
        print(f"File found: '{file_info['name']}' ({file_info['id']})")
        return file_info
    except HttpError as error:
        print(f"An error occured: {error}")
        return None
  
def download_file_content(file_id):
    print("Downloading file from gdrive...")
    service = get_drive_service()
    if not service: return None
    try:
        request = service.files().get_media(fileId=file_id)

        file_buffer = io.BytesIO()

        downloader = MediaIoBaseDownload(file_buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {int(status.progress() * 100)}%.")

        file_buffer.seek(0)
        file_content = file_buffer.read().decode('utf-8') 
        # print(file_content)
        return file_content
    except Exception as e:
        print(f"An error occured downloading file: {e}")
        return None
