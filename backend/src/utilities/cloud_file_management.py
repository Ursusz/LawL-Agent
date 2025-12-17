import os
import io
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"] 

script_dir = Path(__file__).parent.resolve()

SERVICE_ACCOUNT_FILE = script_dir / 'service_account_key.json'

FOLDER_ID = '0APJmM8bO6kV5Uk9PVA'
SUMMARIES_FOLDER_NAME = 'summaries'

# Cache for the Drive service to avoid re-authenticating on every operation
_drive_service_cache = None
_summaries_folder_id_cache = None

def get_drive_service():
    global _drive_service_cache
    
    # Return cached service if available
    if _drive_service_cache is not None:
        return _drive_service_cache
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )

        service = build('drive', 'v3', credentials=creds)
        print("Auth on gdrive was successful.")
        
        # Cache the service for future use
        _drive_service_cache = service
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
        file_id = file.get('id')
        print(f"File with ID-ul: {file_id} was successfully uploaded.")
        return file_id
    except HttpError as error:
        print(f"An error occured: {error}")
        return None
    finally:
        if os.path.exists(file_pth):
            os.remove(file_pth)
            print(f"File '{file_pth}' has been removed from TMP folder.")
        else:
            print(f"File '{file_pth}' does not exist in local storage.")

def update_file_in_cloud(file_pth):
    """Update an existing file in Google Drive or create it if it doesn't exist.
    
    This function searches for a file with the same name and updates it instead of
    creating duplicates. If the file doesn't exist, it creates a new one.
    
    Args:
        file_pth: Path to the local file to upload
        
    Returns:
        file_id: The ID of the updated or created file
    """
    print(f"Updating file {file_pth} in gdrive...")
    service = get_drive_service()
    if not service: return None
    
    try:
        fname = os.path.basename(file_pth)
        
        # Search for existing file
        existing_file = search_file_in_cloud(fname)
        
        media = MediaFileUpload(file_pth, mimetype='application/octet-stream')
        
        if existing_file:
            # Update existing file
            file_id = existing_file['id']
            print(f"Updating existing file with ID: {file_id}")
            file = service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True
            ).execute()
            print(f"File with ID: {file_id} was successfully updated.")
            return file_id
        else:
            # Create new file if it doesn't exist
            print(f"File not found, creating new file...")
            file_metadata = {'name': fname, 'parents': [FOLDER_ID]}
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()
            file_id = file.get('id')
            print(f"File with ID: {file_id} was successfully created.")
            return file_id
            
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
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


def get_or_create_summaries_folder():
    """Find or create the summaries subfolder within the main folder."""
    global _summaries_folder_id_cache
    
    # Return cached folder ID if available
    if _summaries_folder_id_cache is not None:
        return _summaries_folder_id_cache
    
    service = get_drive_service()
    if not service:
        return None
    
    try:
        # Search for existing summaries folder
        query = f"name = '{SUMMARIES_FOLDER_NAME}' and '{FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        results = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
        
        items = results.get("files", [])
        
        if items:
            # Folder exists, cache and return its ID
            folder_id = items[0]['id']
            print(f"Found existing summaries folder: {folder_id}")
            _summaries_folder_id_cache = folder_id
            return folder_id
        else:
            # Create the folder
            file_metadata = {
                'name': SUMMARIES_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [FOLDER_ID]
            }
            folder = service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            folder_id = folder.get('id')
            print(f"Created summaries folder: {folder_id}")
            _summaries_folder_id_cache = folder_id
            return folder_id
            
    except HttpError as error:
        print(f"An error occurred while managing summaries folder: {error}")
        return None

def search_summary_in_cloud(law_ref):
    """Search for a cached summary file by law reference."""
    summaries_folder_id = get_or_create_summaries_folder()
    if not summaries_folder_id:
        return None
    
    service = get_drive_service()
    if not service:
        return None
    
    # Summary files are named: {law_ref}_summary.json
    file_name = f"{law_ref}_summary.json"
    
    try:
        query = f"name = '{file_name}' and '{summaries_folder_id}' in parents"
        results = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
        
        items = results.get("files", [])
        
        if not items:
            print(f"No cached summary found for '{law_ref}'")
            return None
        
        file_info = items[0]
        print(f"Found cached summary: '{file_info['name']}' ({file_info['id']})")
        return file_info
        
    except HttpError as error:
        print(f"An error occurred searching for summary: {error}")
        return None

def save_summary_in_cloud(law_ref, summary_data):
    """Save a summary JSON file to the summaries folder.
    
    Args:
        law_ref: The law reference (e.g., "Legea_120_din_2024")
        summary_data: Dict containing 'law_summary' and 'law_simplified'
    
    Returns:
        The file ID of the saved summary, or None on error
    """
    summaries_folder_id = get_or_create_summaries_folder()
    if not summaries_folder_id:
        return None
    
    service = get_drive_service()
    if not service:
        return None
    
    try:
        # Create temporary JSON file
        import tempfile
        file_name = f"{law_ref}_summary.json"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
            json.dump(summary_data, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = tmp_file.name
        
        # Upload to Drive
        file_metadata = {
            'name': file_name,
            'parents': [summaries_folder_id]
        }
        
        media = MediaFileUpload(tmp_path, mimetype='application/json')
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        file_id = file.get('id')
        print(f"Saved summary to cloud: {file_name} (ID: {file_id})")
        
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        
        return file_id
        
    except Exception as error:
        print(f"An error occurred saving summary: {error}")
        return None

def download_summary_content(file_id):
    """Download and parse a summary JSON file.
    
    Returns:
        Dict containing 'law_summary' and 'law_simplified', or None on error
    """
    print("Downloading summary from gdrive...")
    service = get_drive_service()
    if not service:
        return None
    
    try:
        request = service.files().get_media(fileId=file_id)
        
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading summary {int(status.progress() * 100)}%.")
        
        file_buffer.seek(0)
        file_content = file_buffer.read().decode('utf-8')
        
        # Parse JSON
        summary_data = json.loads(file_content)
        print("Successfully loaded cached summary")
        return summary_data
        
    except Exception as e:
        print(f"An error occurred downloading summary: {e}")
        return None

