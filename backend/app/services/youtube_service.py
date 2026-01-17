import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.config import settings

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    creds = None
    # Check for token file
    if os.path.exists(settings.YOUTUBE_TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(settings.YOUTUBE_TOKEN_FILE, SCOPES)
        except Exception:
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if secret file exists
            if os.path.exists(settings.YOUTUBE_CLIENT_SECRET_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.YOUTUBE_CLIENT_SECRET_FILE, SCOPES)
                # This requires local interaction which might be hard in headless.
                # Ideally user has token. If not, this might fail or hang if not handled.
                # We assume user has the token or can run this once interactively.
                creds = flow.run_local_server(port=0)
            else:
                # If neither exists, we can't upload
                return None
        
        # Save the credentials for the next run
        with open(settings.YOUTUBE_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(file_path, title, description, tags):
    if not settings.UPLOAD_YOUTUBE:
        print("YouTube upload disabled in settings.")
        return {"status": "skipped", "platform": "youtube"}

    youtube = get_authenticated_service()
    if not youtube:
        return {"status": "error", "platform": "youtube", "message": "Authentication failed or missing secrets"}

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '22' # People & Blogs
        },
        'status': {
            'privacyStatus': 'public', 
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    print(f"Uploading to YouTube: {title}")
    
    try:
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"YouTube Upload Progress: {int(status.progress() * 100)}%")
        
        print(f"YouTube Upload Complete. ID: {response.get('id')}")
        return {"status": "success", "platform": "youtube", "data": response}
    except Exception as e:
        print(f"YouTube Upload Failed: {e}")
        return {"status": "error", "platform": "youtube", "message": str(e)}
