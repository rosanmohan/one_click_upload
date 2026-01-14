import requests
import time

def upload_to_instagram(video_url, caption, config=None):
    if config is None:
         return {"status": "error", "platform": "instagram", "message": "No config provided"}

    if not config.get("UPLOAD_INSTAGRAM"):
        return {"status": "skipped", "platform": "instagram"}
    
    account_id = config.get("INSTAGRAM_ACCOUNT_ID")
    access_token = config.get("FACEBOOK_ACCESS_TOKEN")

    if not account_id or not access_token:
         return {"status": "error", "platform": "instagram", "message": "Missing Account ID or Access Token"}

    # Step 1: Create Container
    url = f"https://graph.facebook.com/v18.0/{account_id}/media"
    payload = {
        'access_token': access_token, 
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
            'access_token': access_token,
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
        publish_url = f"https://graph.facebook.com/v18.0/{account_id}/media_publish"
        pub_payload = {
            'access_token': access_token,
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
