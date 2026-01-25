from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import logging
import sys

from app.config import get_settings
from app.services.youtube_service import upload_to_youtube
from app.services.facebook_service import upload_to_facebook
from app.services.instagram_service import upload_to_instagram

# Configure Logging (Stdout for Render)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = FastAPI(title="One Click Social Upload")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

from typing import List, Optional
from app.services.video_processing_service import merge_videos

@app.post("/api/upload")
async def upload_video(
    files: List[UploadFile] = File(None),
    file: UploadFile = File(None),
    description: str = Form(""),
    hashtags: str = Form(""),
    title: str = Form(None),
    merge: bool = Form(False),
    profile_id: str = Form("kids_fun") # Default to existing profile
):
    print(f"--- [START] NEW UPLOAD REQUEST ---", flush=True)
    
    # Load Profile Settings
    current_config = get_settings(profile_id)
    logger.info(f"Using Profile: {profile_id.upper()}")
    
    # 1. Resolve Input Files
    input_files = []
    if files:
        input_files.extend(files)
    if file:
        input_files.append(file)
        
    if not input_files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    logger.info(f"Received {len(input_files)} files. Merge mode: {merge}")

    if not current_config.ALLOW_UPLOAD:
        logger.warning("Uploads are globally disabled (ALLOW_UPLOAD=false)")
        return {"results": [{"platform": "all", "status": "skipped", "message": "Uploads disabled globally"}]}

    saved_file_paths = []
    final_file_path = None
    
    try:
        # Save all files locally first
        for f in input_files:
            file_extension = f.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{file_extension}"
            path = os.path.join(UPLOAD_DIR, filename)
            
            logger.info(f"Saving temp file: {f.filename} -> {path}")
            with open(path, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            saved_file_paths.append(path)
            
    except Exception as e:
        logger.error(f"Failed to save uploaded files: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")

    # 2. Handle Merging vs Single
    try:
        if merge and len(saved_file_paths) > 1:
            logger.info("Merging videos...")
            final_file_path = merge_videos(saved_file_paths, UPLOAD_DIR)
            logger.info(f"Merge successful: {final_file_path}")
            
            # Optional: Clean up input parts? 
            # Usually good practice, but maybe keep for debug?
            # For now, let's keep them (cleaner runs periodically) or delete them.
            # Let's delete to save space (Render free tier is small).
            for p in saved_file_paths:
                try:
                    os.remove(p)
                except:
                    pass
        else:
            # If not merging, we expect only 1 file for this endpoint logic 
            # (Frontend handles looping for non-merge).
            # If multiple sent but merge=False, we just take the first one (fallback)
            # OR we could error. Let's take the first one.
            final_file_path = saved_file_paths[0]
            
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return {"results": [{"platform": "all", "status": "error", "message": f"Processing failed: {str(e)}"}]}

    # 3. Proceed with Upload using final_file_path
    filename = os.path.basename(final_file_path)
    
    # Construct full description
    full_description = f"{description}\n\n{hashtags}" if description else hashtags
    video_title = title if title else (description.split('\n')[0][:100] if description else "Untitled Video")
    
    # Prepare public URL for Instagram
    video_url = f"{current_config.BASE_URL}/static/{filename}"
    logger.info(f"Generated Public URL: {video_url}")
    
    results = []
    
    # 1. YouTube
    if current_config.UPLOAD_YOUTUBE:
        logger.info(f"[YOUTUBE] Starting upload for {profile_id}...")
        try:
            yt_res = upload_to_youtube(final_file_path, video_title, full_description, list(filter(None, hashtags.split())), config=current_config)
            logger.info(f"[YOUTUBE] Result: {yt_res}")
            results.append(yt_res)
        except Exception as e:
            logger.error(f"[YOUTUBE] Critical Failure: {e}", exc_info=True)
            results.append({"status": "error", "platform": "youtube", "message": str(e)})
    else:
        logger.info("[YOUTUBE] Skipped (disabled in config)")
        results.append({"platform": "youtube", "status": "skipped"})
    
    # 2. Facebook
    if current_config.UPLOAD_FACEBOOK:
        logger.info(f"[FACEBOOK] Starting upload for {profile_id}...")
        try:
            fb_res = upload_to_facebook(final_file_path, full_description, video_title, config=current_config)
            logger.info(f"[FACEBOOK] Result: {fb_res}")
            results.append(fb_res)
        except Exception as e:
            logger.error(f"[FACEBOOK] Critical Failure: {e}", exc_info=True)
            results.append({"status": "error", "platform": "facebook", "message": str(e)})
    else:
        logger.info("[FACEBOOK] Skipped (disabled in config)")
        results.append({"platform": "facebook", "status": "skipped"})
    
    # 3. Instagram
    if current_config.UPLOAD_INSTAGRAM:
        logger.info(f"[INSTAGRAM] Starting upload for {profile_id}...")
        try:
            # Try Cloudinary first if credentials exist
            cloudinary_data = None
            if current_config.CLOUDINARY_CLOUD_NAME:
                from app.services.cloudinary_service import upload_video_to_cloudinary, delete_video_from_cloudinary
                logger.info("[INSTAGRAM] Uploading to Cloudinary for valid URL...")
                cloudinary_data = upload_video_to_cloudinary(final_file_path) # Cloudinary service might need config too if creds change per profile. Assuming global for now.
                logger.info(f"[INSTAGRAM] Cloudinary uploaded: {cloudinary_data}")
                
                if cloudinary_data and cloudinary_data.get("url"):
                    # Use Cloudinary URL
                    ig_url = cloudinary_data.get("url")
                    logger.info(f"[INSTAGRAM] Using Cloudinary URL: {ig_url}")
                    ig_res = upload_to_instagram(ig_url, full_description, config=current_config)
                    logger.info(f"[INSTAGRAM] Upload Result: {ig_res}")
                    
                    # Clean up Cloudinary
                    logger.info(f"[INSTAGRAM] Deleting from Cloudinary (ID: {cloudinary_data.get('public_id')})")
                    delete_video_from_cloudinary(cloudinary_data.get("public_id"))
                else:
                    # Fallback to local URL
                    logger.warning("[INSTAGRAM] Cloudinary failed or not configured. Using local URL.")
                    ig_res = upload_to_instagram(video_url, full_description, config=current_config)
                    logger.info(f"[INSTAGRAM] Upload Result: {ig_res}")
                    
                results.append(ig_res)
            else:
                 # No Cloudinary, direct upload
                 ig_res = upload_to_instagram(video_url, full_description, config=current_config)
                 results.append(ig_res)
                 
        except Exception as e:
            logger.error(f"[INSTAGRAM] Critical Failure: {e}", exc_info=True)
            results.append({"status": "error", "platform": "instagram", "message": str(e)})
    else:
        logger.info("[INSTAGRAM] Skipped (disabled in config)")
        results.append({"platform": "instagram", "status": "skipped"})
        
    print(f"--- [END] REQUEST PROCESSED ---", flush=True)
    return {"results": results, "file_path": final_file_path, "public_url": video_url}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
