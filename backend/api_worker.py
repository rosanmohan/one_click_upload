"""
API-Based Scheduled Upload Worker
This worker calls the Render backend API to execute scheduled uploads.
No local database needed - everything is managed through the API.
"""
import os
import sys
import requests
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('RENDER_BACKEND_URL', 'http://localhost:8000')

def safe_print(message: str):
    """Safely print messages with emojis, handling Windows encoding issues."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        ascii_message = message.encode('ascii', 'replace').decode('ascii')
        print(ascii_message)

def execute_scheduled_uploads():
    """Main worker function - calls API to execute pending scheduled uploads."""
    try:
        safe_print("=" * 60)
        safe_print(f"🔄 API-Based Worker Started at {datetime.now(timezone.utc).isoformat()}")
        safe_print(f"   Backend URL: {BACKEND_URL}")
        safe_print("=" * 60)
        
        # Get uploads ready to execute from API
        # We use a retry loop to handle "cold starts" where Render might take 60s+ to wake up
        max_retries = 3
        data = None
        
        from time import sleep
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    safe_print(f"   ⚠️ Attempt {attempt+1}/{max_retries}: Server might be waking up... waiting 10s")
                    sleep(10)
                
                # Increased timeout to 90s for cold starts
                response = requests.get(f"{BACKEND_URL}/api/scheduled/pending/ready", timeout=90)
                response.raise_for_status()
                data = response.json()
                break # Success!
                
            except requests.exceptions.RequestException as e:
                safe_print(f"   ⚠️ Connection failed (Attempt {attempt+1}): {e}")
                if attempt == max_retries - 1:
                    safe_print(f"❌ Failed to fetch ready uploads after {max_retries} attempts.")
                    return
        
        if not data.get('success'):
            safe_print(f"❌ API returned error: {data}")
            return
        
        uploads = data.get('uploads', [])
        safe_print(f"📋 Found {len(uploads)} pending upload(s) to process")
        print()
        
        if not uploads:
            safe_print("✅ No pending uploads to process.")
            return
        
        # Execute each upload via API
        for upload in uploads:
            upload_id = upload['id']
            title = upload['title']
            
            safe_print(f"🎬 Processing Upload: {upload_id}")
            safe_print(f"   Title: {title}")
            safe_print(f"   Scheduled: {upload['scheduled_time']}")
            
            try:
                # Call execute endpoint
                response = requests.post(
                    f"{BACKEND_URL}/api/scheduled/execute/{upload_id}",
                    timeout=300  # 5 minutes for upload
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('success'):
                    safe_print(f"   ✅ Upload COMPLETED successfully!")
                    if result.get('results'):
                        results = result['results']
                        if results.get('youtube'):
                            safe_print(f"      YouTube ID: {results['youtube']}")
                        if results.get('facebook'):
                            safe_print(f"      Facebook ID: {results['facebook']}")
                        if results.get('instagram'):
                            safe_print(f"      Instagram ID: {results['instagram']}")
                else:
                    error_msg = result.get('message', 'Unknown error')
                    safe_print(f"   ❌ Upload FAILED: {error_msg}")
                    if result.get('errors'):
                        for error in result['errors']:
                            safe_print(f"      - {error}")
                
            except requests.exceptions.Timeout:
                safe_print(f"   ⏱️ Upload TIMEOUT (may still be processing)")
            except requests.exceptions.RequestException as e:
                safe_print(f"   ❌ API Error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                     safe_print(f"      Server Response: {e.response.text}")
            except Exception as e:
                safe_print(f"   ❌ Unexpected error: {e}")
            
            print()  # Blank line for readability
        
        safe_print("=" * 60)
        safe_print(f"✅ Worker Completed at {datetime.now(timezone.utc).isoformat()}")
        safe_print("=" * 60)
        
    except Exception as e:
        safe_print(f"❌ Worker failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    execute_scheduled_uploads()
