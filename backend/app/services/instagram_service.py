import requests
import time
from app.config import settings

def upload_to_instagram(video_url, caption):
    if not settings.UPLOAD_INSTAGRAM:
        return {"status": "skipped", "platform": "instagram"}
    
    if not settings.INSTAGRAM_ACCOUNT_ID or not settings.FACEBOOK_ACCESS_TOKEN:
         return {"status": "error", "platform": "instagram", "message": "Missing Account ID or Access Token"}

    # Step 1: Create Container
    url = f"https://graph.facebook.com/v18.0/{settings.INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        'access_token': settings.FACEBOOK_ACCESS_TOKEN, 
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption
    }
    
    try:
        print(f"Creating Instagram Container: {url}")
        print(f"Payload: {payload}")
        response = requests.post(url, data=payload)
        print(f"Container Response: {response.status_code} - {response.text}")
        
        if response.status_code != 200:
             return {"status": "error", "platform": "instagram", "message": f"Create Container Failed: {response.text}"}
        
        container_id = response.json().get('id')
        print(f"Container ID: {container_id}. Waiting for processing...")
        
        # Step 2: Wait for processing
        status_url = f"https://graph.facebook.com/v18.0/{container_id}"
        params = {
            'access_token': settings.FACEBOOK_ACCESS_TOKEN,
            'fields': 'status_code'
        }
        
        attempts = 0
        while attempts < 20: # Wait up to 100 seconds
            status_res = requests.get(status_url, params=params)
            status_data = status_res.json()
            status_code = status_data.get('status_code')
            print(f"Processing Status: {status_code}")
            
            if status_code == 'FINISHED':
                break
            elif status_code == 'ERROR':
                 return {"status": "error", "platform": "instagram", "message": "Instagram processing failed"}
            
            time.sleep(5)
            attempts += 1
            
        # Step 3: Publish
        print("Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v18.0/{settings.INSTAGRAM_ACCOUNT_ID}/media_publish"
        pub_payload = {
            'access_token': settings.FACEBOOK_ACCESS_TOKEN,
            'creation_id': container_id
        }
        pub_res = requests.post(publish_url, data=pub_payload)
        print(f"Publish Response: {pub_res.text}")
        
        if pub_res.status_code == 200:
            return {"status": "success", "platform": "instagram", "data": pub_res.json()}
        else:
             return {"status": "error", "platform": "instagram", "message": f"Publish Failed: {pub_res.text}"}

    except Exception as e:
        print(f"Instagram Upload Failed: {e}")
        return {"status": "error", "platform": "instagram", "message": str(e)}
