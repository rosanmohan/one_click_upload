import requests
import time
import json
from app.config import settings

def upload_to_instagram(video_url, caption, config=settings):
    if not config.UPLOAD_INSTAGRAM:
        return {"status": "skipped", "platform": "instagram"}
    
    if not config.INSTAGRAM_ACCOUNT_ID or not config.FACEBOOK_ACCESS_TOKEN:
         return {"status": "error", "platform": "instagram", "message": "Missing Account ID or Access Token"}

    # Step 1: Create Container
    url = f"https://graph.facebook.com/v18.0/{config.INSTAGRAM_ACCOUNT_ID}/media"
    payload = {
        'access_token': config.FACEBOOK_ACCESS_TOKEN, 
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption
    }
    
    try:
        print(f"Creating Instagram Container: {url}")
        # Be careful not to log full access tokens in prod, but for debug it's useful (masked)
        masked_payload = payload.copy()
        masked_payload['access_token'] = '***'
        print(f"Payload: {masked_payload}")
        
        response = requests.post(url, data=payload)
        
        print(f"Container Response: {response.status_code}")
        try:
            res_json = response.json()
            print(f"Response Body: {res_json}")
            if 'error' in res_json:
                error_details = res_json['error']
                print(f"Instagram Error Details: {json.dumps(error_details, indent=2)}")
        except:
             print(f"Response Text: {response.text}")

        if response.status_code != 200:
             return {"status": "error", "platform": "instagram", "message": f"Create Container Failed: {response.text}"}
        
        container_id = response.json().get('id')
        print(f"Container ID: {container_id}. Waiting for processing...")
        
        # Step 2: Wait for processing
        status_url = f"https://graph.facebook.com/v18.0/{container_id}"
        params = {
            'access_token': config.FACEBOOK_ACCESS_TOKEN,
            'fields': 'status_code,status'
        }
        
        attempts = 0
        while attempts < 20: # Wait up to 100 seconds
            status_res = requests.get(status_url, params=params)
            status_data = status_res.json()
            status_code = status_data.get('status_code')
            print(f"Processing Status: {status_code} (Details: {status_data})")
            
            if status_code == 'FINISHED':
                break
            elif status_code == 'ERROR':
                 error_msg = f"Instagram processing failed. Status Data: {status_data}"
                 print(error_msg)
                 return {"status": "error", "platform": "instagram", "message": error_msg}
            
            time.sleep(5)
            attempts += 1
            
        # Step 3: Publish
        print("Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v18.0/{config.INSTAGRAM_ACCOUNT_ID}/media_publish"
        pub_payload = {
            'access_token': config.FACEBOOK_ACCESS_TOKEN,
            'creation_id': container_id
        }
        pub_res = requests.post(publish_url, data=pub_payload)
        
        print(f"Publish Response: {pub_res.status_code}")
        try:
            pub_json = pub_res.json()
            print(f"Publish Body: {pub_json}")
            if 'error' in pub_json:
                 print(f"Publish Error Details: {json.dumps(pub_json['error'], indent=2)}")
        except:
            print(f"Publish Text: {pub_res.text}")
        
        if pub_res.status_code == 200:
            return {"status": "success", "platform": "instagram", "data": pub_res.json()}
        else:
             return {"status": "error", "platform": "instagram", "message": f"Publish Failed: {pub_res.text}"}

    except Exception as e:
        print(f"Instagram Upload Failed (Exception): {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "platform": "instagram", "message": str(e)}
