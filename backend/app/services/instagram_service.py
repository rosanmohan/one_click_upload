import requests
import time
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def upload_to_instagram(video_url, caption, config=settings):
    if not config.UPLOAD_INSTAGRAM:
        logger.info("Instagram upload disabled in settings.")
        return {"status": "skipped", "platform": "instagram"}
    
    if not config.INSTAGRAM_ACCOUNT_ID or not config.FACEBOOK_ACCESS_TOKEN:
         logger.error("Instagram upload failed: Missing Account ID or Access Token")
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
        logger.info(f"Creating Instagram Container: {url}")
        
        response = requests.post(url, data=payload)
        
        logger.info(f"Container Response: {response.status_code}")
        try:
            res_json = response.json()
            if 'error' in res_json:
                error_details = res_json['error']
                logger.error(f"Instagram Error Details: {json.dumps(error_details, indent=2)}")
        except Exception:
             logger.warning(f"Could not parse response body: {response.text}")

        if response.status_code != 200:
             logger.error(f"Create Container Failed: {response.text}")
             return {"status": "error", "platform": "instagram", "message": f"Create Container Failed: {response.text}"}
        
        container_id = response.json().get('id')
        logger.info(f"Container ID: {container_id}. Waiting for processing...")
        
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
            logger.info(f"Processing Status: {status_code}")
            
            if status_code == 'FINISHED':
                break
            elif status_code == 'ERROR':
                 error_msg = f"Instagram processing failed. Status Data: {status_data}"
                 logger.error(error_msg)
                 return {"status": "error", "platform": "instagram", "message": error_msg}
            
            time.sleep(5)
            attempts += 1
            
        # Step 3: Publish
        logger.info("Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v18.0/{config.INSTAGRAM_ACCOUNT_ID}/media_publish"
        pub_payload = {
            'access_token': config.FACEBOOK_ACCESS_TOKEN,
            'creation_id': container_id
        }
        pub_res = requests.post(publish_url, data=pub_payload)
        
        logger.info(f"Publish Response: {pub_res.status_code}")
        try:
            pub_json = pub_res.json()
            if 'error' in pub_json:
                 logger.error(f"Publish Error Details: {json.dumps(pub_json['error'], indent=2)}")
        except Exception:
            logger.error(f"Publish Text: {pub_res.text}")
        
        if pub_res.status_code == 200:
            logger.info("Instagram publish successful.")
            return {"status": "success", "platform": "instagram", "data": pub_res.json()}
        else:
             logger.error(f"Publish Failed: {pub_res.text}")
             return {"status": "error", "platform": "instagram", "message": f"Publish Failed: {pub_res.text}"}

    except Exception as e:
        logger.error(f"Instagram Upload Failed (Exception): {e}", exc_info=True)
        return {"status": "error", "platform": "instagram", "message": str(e)}

