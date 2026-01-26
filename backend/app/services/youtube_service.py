import os
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service(config=settings):
    creds = None
    # Check for token file
    if os.path.exists(config.YOUTUBE_TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(config.YOUTUBE_TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load credentials from file {config.YOUTUBE_TOKEN_FILE}: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired YouTube credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                creds = None
        else:
            # Check if secret file exists
            if os.path.exists(config.YOUTUBE_CLIENT_SECRET_FILE):
                logger.info(f"Initiating new OAuth flow using secret file: {config.YOUTUBE_CLIENT_SECRET_FILE}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.YOUTUBE_CLIENT_SECRET_FILE, SCOPES)
                # This requires local interaction which might be hard in headless.
                # We assume user has the token or can run this once interactively.
                # Render deployment: This will fail if no token and no interactive shell.
                try:
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"OAuth flow failed: {e}")
                    return None
            else:
                logger.error(f"No token file ({config.YOUTUBE_TOKEN_FILE}) and no secret file ({config.YOUTUBE_CLIENT_SECRET_FILE}) found.")
                # If neither exists, we can't upload
                return None
        
        # Save the credentials for the next run
        if creds:
            try:
                with open(config.YOUTUBE_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                logger.info(f"Saved new YouTube credentials to {config.YOUTUBE_TOKEN_FILE}")
            except Exception as e:
                logger.error(f"Failed to save credentials: {e}")

    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Failed to build YouTube service: {e}")
        return None

def upload_to_youtube(file_path, title, description, tags, config=settings):
    if not config.UPLOAD_YOUTUBE:
        logger.info("YouTube upload disabled in settings.")
        return {"status": "skipped", "platform": "youtube"}

    youtube = get_authenticated_service(config)
    if not youtube:
        error_msg = "YouTube Authentication failed. Check logs for missing token/secret files."
        logger.error(error_msg)
        return {"status": "error", "platform": "youtube", "message": error_msg}

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

    logger.info(f"Uploading to YouTube: {title}")
    
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
                progress = int(status.progress() * 100)
                # Avoid spamming logs, log every 25% or so if possible, but for now just info
                logger.info(f"YouTube Upload Progress: {progress}%")
        
        video_id = response.get('id')
        logger.info(f"YouTube Upload Complete. ID: {video_id}")
        return {"status": "success", "platform": "youtube", "data": response}
    except Exception as e:
        logger.error(f"YouTube Upload Failed: {e}", exc_info=True)
        return {"status": "error", "platform": "youtube", "message": f"{str(e)}"}

