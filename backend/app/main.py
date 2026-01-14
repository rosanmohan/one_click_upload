@app.post("/api/upload")
async def upload_video(
    file: UploadFile = File(...),
    description: str = Form(""),
    hashtags: str = Form(""),
    title: str = Form(None),
    profile_id: str = Form(None)
):
    logger.info(f"--- NEW UPLOAD REQUEST ---")
    logger.info(f"Filename: {file.filename}")
    logger.info(f"Profile ID: {profile_id}")
    
    # Load profile config
    profile_config = settings.get_profile_config(profile_id)
    
    if not profile_config.get("ALLOW_UPLOAD"):
        logger.warning(f"Uploads disabled for profile {profile_id} (ALLOW_UPLOAD=false)")
        return {"results": [{"platform": "all", "status": "skipped", "message": "Uploads disabled for this profile"}]}

    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    try:
        logger.info(f"Saving file to {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved successfully. Size: {os.path.getsize(file_path)} bytes")
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="File save failed")
        
    # Construct full description
    full_description = f"{description}\n\n{hashtags}" if description else hashtags
    # Use title if provided, else use first line of description (truncated)
    video_title = title if title else (description.split('\n')[0][:100] if description else "Untitled Video")
    
    # Prepare public URL for Instagram
    video_url = f"{settings.BASE_URL}/static/{filename}"
    logger.info(f"Generated Public URL: {video_url}")
    
    results = []
    
    # 1. YouTube
    if profile_config.get("UPLOAD_YOUTUBE"):
        logger.info(f"[YOUTUBE] Starting upload for profile {profile_id}...")
        try:
            yt_res = upload_to_youtube(file_path, video_title, full_description, list(filter(None, hashtags.split())), profile_config)
            logger.info(f"[YOUTUBE] Result: {yt_res}")
            results.append(yt_res)
        except Exception as e:
            logger.error(f"[YOUTUBE] Critical Failure: {e}", exc_info=True)
            results.append({"status": "error", "platform": "youtube", "message": str(e)})
    else:
        logger.info("[YOUTUBE] Skipped (disabled in profile config)")
        results.append({"platform": "youtube", "status": "skipped"})
        
    # 2. Facebook
    if profile_config.get("UPLOAD_FACEBOOK"):
        logger.info(f"[FACEBOOK] Starting upload for profile {profile_id}...")
        try:
            fb_res = upload_to_facebook(file_path, full_description, video_title, profile_config)
            logger.info(f"[FACEBOOK] Result: {fb_res}")
            results.append(fb_res)
        except Exception as e:
            logger.error(f"[FACEBOOK] Critical Failure: {e}", exc_info=True)
            results.append({"status": "error", "platform": "facebook", "message": str(e)})
    else:
        logger.info("[FACEBOOK] Skipped (disabled in profile config)")
        results.append({"platform": "facebook", "status": "skipped"})
        
    # 3. Instagram
    if profile_config.get("UPLOAD_INSTAGRAM"):
        logger.info(f"[INSTAGRAM] Starting upload for profile {profile_id}...")
        try:
            # Try Cloudinary first if credentials exist (Global setting usually, but can be per profile if needed)
            cloudinary_data = None
            if settings.CLOUDINARY_CLOUD_NAME:
                from app.services.cloudinary_service import upload_video_to_cloudinary, delete_video_from_cloudinary
                logger.info("[INSTAGRAM] Uploading to Cloudinary for valid URL...")
                cloudinary_data = upload_video_to_cloudinary(file_path)
                logger.info(f"[INSTAGRAM] Cloudinary uploaded: {cloudinary_data}")
                
            if cloudinary_data and cloudinary_data.get("url"):
                # Use Cloudinary URL
                ig_url = cloudinary_data.get("url")
                logger.info(f"[INSTAGRAM] Using Cloudinary URL: {ig_url}")
                ig_res = upload_to_instagram(ig_url, full_description, profile_config)
                logger.info(f"[INSTAGRAM] Upload Result: {ig_res}")
                
                # Clean up Cloudinary
                logger.info(f"[INSTAGRAM] Deleting from Cloudinary (ID: {cloudinary_data.get('public_id')})")
                delete_video_from_cloudinary(cloudinary_data.get("public_id"))
            else:
                # Fallback to local URL (won't work for real Instagram unless tunnelled)
                logger.warning("[INSTAGRAM] Cloudinary failed or not configured. Using local URL (likely to fail via API).")
                ig_res = upload_to_instagram(video_url, full_description, profile_config)
                logger.info(f"[INSTAGRAM] Upload Result: {ig_res}")
                
            results.append(ig_res)
        except Exception as e:
            logger.error(f"[INSTAGRAM] Critical Failure: {e}", exc_info=True)
            results.append({"status": "error", "platform": "instagram", "message": str(e)})
    else:
        logger.info("[INSTAGRAM] Skipped (disabled in profile config)")
        results.append({"platform": "instagram", "status": "skipped"})
        
    return {"results": results, "file_path": file_path, "public_url": video_url}
