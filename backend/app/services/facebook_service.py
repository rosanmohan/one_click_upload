import requests
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def upload_to_facebook(file_path, description, title=None, config=settings):
    if not config.UPLOAD_FACEBOOK:
        logger.info("Facebook upload disabled in settings.")
        return {"status": "skipped", "platform": "facebook"}

    if not config.FACEBOOK_PAGE_ID or not config.FACEBOOK_ACCESS_TOKEN:
         logger.error("Facebook upload failed: Missing Page ID or Access Token")
         return {"status": "error", "platform": "facebook", "message": "Missing Page ID or Access Token"}

    url = f"https://graph-video.facebook.com/v18.0/{config.FACEBOOK_PAGE_ID}/videos"
    
    payload = {
        'access_token': config.FACEBOOK_ACCESS_TOKEN,
        'description': description,
        'title': title or description[:50]
    }
    
    # We open the file here. Caller should ensure it exists.
    try:
        logger.info(f"Uploading to Facebook: {url} (Page ID: {config.FACEBOOK_PAGE_ID})")
        with open(file_path, 'rb') as file_data:
            files = {
                'source': file_data
            }
            response = requests.post(url, data=payload, files=files)
            
        logger.info(f"Facebook Response: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Facebook upload successful.")
            return {"status": "success", "platform": "facebook", "data": response.json()}
        else:
             logger.error(f"Facebook upload failed: {response.text}")
             return {"status": "error", "platform": "facebook", "message": response.text}
    except Exception as e:
         logger.error(f"Facebook Upload Failed (Exception): {e}", exc_info=True)
         return {"status": "error", "platform": "facebook", "message": str(e)}

