import requests
import os

def upload_to_facebook(file_path, description, title=None, config=None):
    if config is None:
        # Should not happen in new flow
        return {"status": "error", "platform": "facebook", "message": "No config provided"}

    if not config.get("UPLOAD_FACEBOOK"):
        return {"status": "skipped", "platform": "facebook"}

    page_id = config.get("FACEBOOK_PAGE_ID")
    access_token = config.get("FACEBOOK_ACCESS_TOKEN")

    if not page_id or not access_token:
         return {"status": "error", "platform": "facebook", "message": "Missing Page ID or Access Token"}

    url = f"https://graph-video.facebook.com/v18.0/{page_id}/videos"
    
    payload = {
        'access_token': access_token,
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
