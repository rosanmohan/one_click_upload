import requests
import os
from app.config import settings

def upload_to_facebook(file_path, description, title=None, config=settings):
    if not config.UPLOAD_FACEBOOK:
        return {"status": "skipped", "platform": "facebook"}

    if not config.FACEBOOK_PAGE_ID or not config.FACEBOOK_ACCESS_TOKEN:
         return {"status": "error", "platform": "facebook", "message": "Missing Page ID or Access Token"}

    url = f"https://graph-video.facebook.com/v18.0/{config.FACEBOOK_PAGE_ID}/videos"
    
    payload = {
        'access_token': config.FACEBOOK_ACCESS_TOKEN,
        'description': description,
        'title': title or description[:50]
    }
    
    # We open the file here. Caller should ensure it exists.
    try:
        print(f"Uploading to Facebook: {url}")
        with open(file_path, 'rb') as file_data:
            files = {
                'source': file_data
            }
            response = requests.post(url, data=payload, files=files)
            
        print(f"Facebook Response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            return {"status": "success", "platform": "facebook", "data": response.json()}
        else:
             return {"status": "error", "platform": "facebook", "message": response.text}
    except Exception as e:
         print(f"Facebook Upload Failed: {e}")
         return {"status": "error", "platform": "facebook", "message": str(e)}
