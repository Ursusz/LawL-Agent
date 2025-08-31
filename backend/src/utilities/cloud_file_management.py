import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
current_folder = './utilities'
credentials_location = os.path.join(current_folder, 'credentials.json')
token_location = os.path.join(current_folder, 'token.json')

def get_drive_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_location):
        creds = Credentials.from_authorized_user_file(token_location, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_location, SCOPES
            )
            creds = flow.run_local_server(port=0, acces_type='offline', prompt='consent')
        # Save the credentials for the next run
        with open(token_location, "w") as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def save_file_in_cloud(file_pth):
    service = get_drive_service()
    try:
        fname = os.path.basename(file_pth)
        file_metadata = {
            'name': fname
        }
        media = MediaFileUpload(file_pth, mimetype='text/plain')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Fisierul cu ID-ul: {file.get('id')} a fost incarcat cu succes.")
    except HttpError as error:
        print(f"An error occured: {error}")
    finally:
        if os.path.exists(file_pth):
            os.remove(file_pth)
            print(f"File '{file_pth}' has been removed from TMP folder.")
        else:
            print(f"File '{file_pth}' does not exist in local storage.")

def search_file_in_cloud(file_name):
    service = get_drive_service()
    fname = os.path.basename(file_name)
    try:
        query = f"name = '{fname}'"
        results = (
            service.files()
            .list(q=query, spaces="drive", fields="nextPageToken, files(id, name, mimeType)")
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
    service = get_drive_service()
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
        return file_content
    except Exception as e:
        print(f"An error occured downloading file: {e}")
        return None