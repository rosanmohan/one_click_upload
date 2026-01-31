from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import os
import shutil

from app.database import (
    create_scheduled_upload,
    get_scheduled_uploads,
    delete_scheduled_upload,
    get_upload_by_id
)

router = APIRouter(prefix="/api/scheduled", tags=["scheduled"])

UPLOAD_DIR = os.path.join(os.getcwd(), "scheduled_videos")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload")
async def schedule_upload(
    file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File(None),
    title: str = Form(...),
    description: str = Form(""),
    hashtags: str = Form(""),
    scheduled_time: str = Form(...),  # ISO 8601 format: "2026-01-28T15:30:00"
    profile_id: str = Form("kids_fun"),
    upload_youtube: bool = Form(False),
    upload_facebook: bool = Form(False),
    upload_instagram: bool = Form(False),
    merge_videos: bool = Form(False)
):
    """
    Schedule a video upload for a future date/time.
    
    - **file**: Single file (for backward compatibility)
    - **files**: Multiple files (for merging)
    - **scheduled_time**: ISO 8601 format (e.g., "2026-01-28T15:30:00")
    - **profile_id**: Profile to use for upload (default: "kids_fun")
    - **upload_youtube/facebook/instagram**: Enable/disable specific platforms
    - **merge_videos**: If True and multiple files, merge them before upload
    """
    
    # Validate scheduled time is in the future
    try:
        scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        if scheduled_dt <= current_time:
            raise HTTPException(
                status_code=400,
                detail="Scheduled time must be in the future"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid datetime format. Use ISO 8601 format: {str(e)}"
        )
    
    # Validate at least one platform is selected
    if not any([upload_youtube, upload_facebook, upload_instagram]):
        raise HTTPException(
            status_code=400,
            detail="At least one upload platform must be selected"
        )
    
    # Determine if single or multiple files
    upload_files = []
    if file:
        upload_files = [file]
    elif files:
        upload_files = files
    else:
        raise HTTPException(
            status_code=400,
            detail="At least one video file must be provided"
        )
    
    # Generate unique ID
    upload_id = str(uuid.uuid4())
    
    # Save video file(s) locally first, then upload to Cloudinary for persistence
    saved_files = []
    updated_video_paths = []
    
    # Import Cloudinary service
    from app.services.cloudinary_service import upload_video_to_cloudinary
    
    try:
        # 1. Save locally
        for idx, upload_file in enumerate(upload_files):
            file_extension = os.path.splitext(upload_file.filename)[1]
            if len(upload_files) == 1:
                video_filename = f"{upload_id}{file_extension}"
            else:
                video_filename = f"{upload_id}_part{idx+1}{file_extension}"
            video_path = os.path.join(UPLOAD_DIR, video_filename)
            
            with open(video_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            saved_files.append(video_path)
            
        # 2. Upload to Cloudinary (Critical for persistence on Render Free Tier)
        from app.config import get_settings
        settings_config = get_settings(profile_id)
        
        # Only upload if Cloudinary is configured
        if settings_config.CLOUDINARY_CLOUD_NAME and settings_config.CLOUDINARY_API_KEY:
            for saved_path in saved_files:
                cld_result = upload_video_to_cloudinary(saved_path)
                if cld_result and cld_result.get('url'):
                    updated_video_paths.append(cld_result.get('url'))
                    # Remove local file to save space (it's safe in cloud now)
                    try:
                        os.remove(saved_path)
                    except:
                        pass
                else:
                    # Fallback to local path if Cloudinary fails (risky on free tier)
                    updated_video_paths.append(saved_path)
        else:
             # No Cloudinary configured, keep local paths
             updated_video_paths = saved_files
             
    except Exception as e:
        # Clean up any saved files on error
        for saved_path in saved_files:
            if os.path.exists(saved_path):
                try:
                    os.remove(saved_path)
                except:
                    pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save/upload video file: {str(e)}"
        )
    
    # Store multiple file paths as JSON if multiple files, otherwise single path
    import json
    if len(updated_video_paths) == 1:
        final_video_path = updated_video_paths[0]
        # Filename is just for reference/display
        final_video_filename = os.path.basename(saved_files[0]) if saved_files else "video.mp4"
    else:
        # Store all paths (URLs) as JSON - worker will handle them
        final_video_path = json.dumps(updated_video_paths)
        final_video_filename = f"{upload_id}_multipart.json"

    # Create database entry
    try:
        result = create_scheduled_upload(
            upload_id=upload_id,
            profile_id=profile_id,
            title=title,
            description=description,
            hashtags=hashtags,
            scheduled_time=scheduled_time,
            video_filename=final_video_filename,
            video_path=final_video_path,
            merge_videos=merge_videos,
            upload_youtube=upload_youtube,
            upload_facebook=upload_facebook,
            upload_instagram=upload_instagram
        )
        
        return JSONResponse(content={
            "success": True,
            "message": f"Upload scheduled for {scheduled_time}",
            "upload_id": upload_id,
            "data": result
        })
    
    except Exception as e:
        # Clean up video file(s) if database insert fails
        for saved_path in saved_files:
            if os.path.exists(saved_path):
                os.remove(saved_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule upload: {str(e)}"
        )

@router.get("/list")
async def list_scheduled_uploads(
    profile_id: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Get all scheduled uploads with optional filtering.
    
    - **profile_id**: Filter by profile (optional)
    - **status**: Filter by status: pending, completed, failed (optional)
    """
    try:
        uploads = get_scheduled_uploads(profile_id=profile_id, status=status)
        return JSONResponse(content={
            "success": True,
            "count": len(uploads),
            "uploads": uploads
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve scheduled uploads: {str(e)}"
        )

@router.get("/{upload_id}")
async def get_scheduled_upload(upload_id: str):
    """Get details of a specific scheduled upload."""
    try:
        upload = get_upload_by_id(upload_id)
        if not upload:
            raise HTTPException(
                status_code=404,
                detail="Scheduled upload not found"
            )
        return JSONResponse(content={
            "success": True,
            "upload": upload
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve scheduled upload: {str(e)}"
        )

@router.delete("/{upload_id}")
async def cancel_scheduled_upload(upload_id: str):
    """
    Cancel a scheduled upload.
    
    Only pending or failed uploads can be deleted.
    """
    try:
        success = delete_scheduled_upload(upload_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Upload not found or cannot be deleted (already completed)"
            )
        
        return JSONResponse(content={
            "success": True,
            "message": "Scheduled upload cancelled successfully"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel scheduled upload: {str(e)}"
        )

@router.post("/execute/{upload_id}")
async def execute_scheduled_upload(upload_id: str):
    """
    Execute a specific scheduled upload now.
    
    This endpoint is called by the GitHub Actions worker to execute scheduled uploads.
    It loads the upload details, executes the upload to platforms, and updates the status.
    """
    import json
    try:
        # Get upload details
        upload = get_upload_by_id(upload_id)
        if not upload:
            raise HTTPException(
                status_code=404,
                detail="Scheduled upload not found"
            )
        
        # Check if already completed
        if upload['status'] == 'completed':
            return JSONResponse(content={
                "success": True,
                "message": "Upload already completed",
                "upload_id": upload_id
            })
        
        # Import services
        from app.config import get_settings
        from app.services.video_processing_service import merge_videos
        from app.services.youtube_service import upload_to_youtube
        from app.services.facebook_service import upload_to_facebook
        from app.services.instagram_service import upload_to_instagram
        from app.services.cloudinary_service import upload_video_to_cloudinary, delete_video_from_cloudinary
        from app.database import update_upload_status
        
        profile_id = upload['profile_id']
        title = upload['title']
        description = upload['description']
        hashtags = upload['hashtags']
        video_path = upload['video_path']
        merge_videos_flag = upload.get('merge_videos', 0)
        
        # Handle multiple files
        video_files = []
        downloaded_temp_files = [] # Keep track to delete later
        merged_video_path = None
        
        # Helper to download file if URL
        import requests
        import tempfile
        
        def get_local_file_path(path_or_url):
            if path_or_url.startswith('http'):
                try:
                    # Download to temp file
                    print(f"Downloading from Cloudinary: {path_or_url}")
                    suffix = os.path.splitext(path_or_url)[1]
                    if not suffix or len(suffix) > 5: # basic check
                         suffix = '.mp4'
                         
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        with requests.get(path_or_url, stream=True) as r:
                            r.raise_for_status()
                            shutil.copyfileobj(r.raw, tmp)
                        temp_path = tmp.name
                        downloaded_temp_files.append(temp_path)
                        return temp_path
                except Exception as e:
                    raise Exception(f"Failed to download video from URL: {e}")
            return path_or_url
        
        print(f"DEBUG: Processing video_path: {video_path!r} (Type: {type(video_path)})")
        
        try:
            # Try to parse as JSON (multiple files)
            parsed_files = None
            
            # 0. Check if already a list (unlikely from DB but possible)
            if isinstance(video_path, list):
                parsed_files = video_path
            
            # 1. Try JSON
            if parsed_files is None:
                try:
                    parsed_files = json.loads(video_path)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # 2. Try AST (for single quotes or Python list string)
            if parsed_files is None:
                try:
                    if isinstance(video_path, str) and video_path.strip().startswith('[') and video_path.strip().endswith(']'):
                        import ast
                        parsed_files = ast.literal_eval(video_path)
                        print("DEBUG: Parsed video_path using ast.literal_eval")
                except:
                    pass
            
            # 3. Ultimate Fallback: Regex to find URLs
            if parsed_files is None and isinstance(video_path, str) and 'http' in video_path:
                import re
                # Find http/https URLs that end with a quote or whitespace
                # This pattern looks for http(s)://... until a quote, bracket, or whitespace
                found_urls = re.findall(r'https?://[^"\'\]\s]+', video_path)
                if found_urls:
                    parsed_files = found_urls
                    print(f"DEBUG: Parsed video_path using Regex, found {len(parsed_files)} URLs")

            # Validate result
            if parsed_files is None:
                raise ValueError("Could not parse video_path")

            # Ensure it's a list
            if not isinstance(parsed_files, list):
                parsed_files = [parsed_files]
                
            # Convert all paths/URLs to local files
            for vf in parsed_files:
                local_path = get_local_file_path(vf)
                if not os.path.exists(local_path):
                     print(f"DEBUG: Failed to find/download: {local_path} (Origin: {vf})")
                     raise HTTPException(
                        status_code=404,
                        detail=f"Video file not found locally or failed to download: {vf}"
                    )
                video_files.append(local_path)
            
            # Merge videos if merge_videos flag is True
            if merge_videos_flag and len(video_files) > 1:
                merged_video_path = merge_videos(video_files)
                video_path = merged_video_path
            else:
                # If not merging, use first video
                video_path = video_files[0]
                
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"DEBUG: Parsing failed: {e}. Treating as single path.")
            # Single file path (not JSON)
            local_path = get_local_file_path(video_path)
            if not os.path.exists(local_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Video file not found: {video_path} (Parse Error: {e})"
                )
            video_files = [local_path]
            video_path = local_path
        
        # Verify final video exists
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=404,
                detail=f"Video file not found: {video_path}"
            )
        
        # Load profile settings
        settings = get_settings(profile_id)
        
        # Track upload results
        results = {
            'youtube': None,
            'facebook': None,
            'instagram': None
        }
        errors = []
        
        # Execute uploads to enabled platforms
        if upload.get('upload_youtube') and settings.UPLOAD_YOUTUBE:
            try:
                # Fix: Use correct argument names for YouTube
                yt_result = upload_to_youtube(
                    file_path=video_path,
                    title=title,
                    description=description,
                    tags=hashtags,
                    config=settings
                )
                if yt_result.get('status') == 'success':
                    # Extract video ID from data if available, or use a placeholder
                    data = yt_result.get('data', {})
                    video_id = data.get('id', 'uploaded')
                    results['youtube'] = video_id
                else:
                    errors.append(f"YouTube: {yt_result.get('message', 'Unknown error')}")
            except Exception as e:
                errors.append(f"YouTube: {str(e)}")
        
        if upload.get('upload_facebook') and settings.UPLOAD_FACEBOOK:
            try:
                # Fix: Use correct argument names for Facebook
                fb_result = upload_to_facebook(
                    file_path=video_path,
                    title=title,
                    description=description,
                    config=settings
                )
                if fb_result.get('status') == 'success':
                    data = fb_result.get('data', {})
                    post_id = data.get('id', 'uploaded')
                    results['facebook'] = post_id
                else:
                    errors.append(f"Facebook: {fb_result.get('message', 'Unknown error')}")
            except Exception as e:
                errors.append(f"Facebook: {str(e)}")
        
        if upload.get('upload_instagram') and settings.UPLOAD_INSTAGRAM:
            try:
                # Fix: Instagram needs a public URL, so upload to Cloudinary first
                cld_result = upload_video_to_cloudinary(video_path)
                
                if cld_result and cld_result.get('url'):
                    video_url = cld_result.get('url')
                    
                    ig_result = upload_to_instagram(
                        video_url=video_url,
                        caption=description,
                        config=settings
                    )
                    
                    if ig_result.get('status') == 'success':
                        data = ig_result.get('data', {})
                        media_id = data.get('id', 'uploaded')
                        results['instagram'] = media_id
                    else:
                        errors.append(f"Instagram: {ig_result.get('message', 'Unknown error')}")
                        
                    # Cleanup Cloudinary (optional, but good practice if checking storage)
                    # delete_video_from_cloudinary(cld_result.get('public_id'))
                else:
                    errors.append("Instagram: Failed to upload to Cloudinary (required for Instagram)")
                    
            except Exception as e:
                errors.append(f"Instagram: {str(e)}")
        
        # Determine final status
        successful_uploads = sum(1 for v in results.values() if v is not None)
        
        if errors and successful_uploads == 0:
            # All failed
            status = 'failed'
            error_message = "; ".join(errors)
        elif errors:
            # Some failed
            status = 'completed'
            error_message = f"Partial success. Errors: {'; '.join(errors)}"
        else:
            # All successful
            status = 'completed'
            error_message = None
        
        # Update database
        update_upload_status(
            upload_id=upload_id,
            status=status,
            error_message=error_message,
            youtube_video_id=results['youtube'],
            facebook_post_id=results['facebook'],
            instagram_media_id=results['instagram']
        )
        
        # Clean up video files
        try:
            # Clean up final video
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            
            # Clean up individual parts if merged
            if merged_video_path and len(video_files) > 1:
                for vf in video_files:
                    if vf and os.path.exists(vf):
                        os.remove(vf)
            
            # Clean up explicit temp files (redundancy check)
            for temp_f in downloaded_temp_files:
                if temp_f and os.path.exists(temp_f):
                    try:
                        os.remove(temp_f)
                    except:
                        pass
        except Exception:
            # Don't fail the request if cleanup fails
            pass
        
        return JSONResponse(content={
            "success": status == 'completed',
            "message": "Upload executed" if status == 'completed' else "Upload failed",
            "upload_id": upload_id,
            "status": status,
            "results": results,
            "errors": errors if errors else None
        })
        
    except HTTPException:
        raise
    except Exception as e:
        # Update status to failed
        try:
            from app.database import update_upload_status
            update_upload_status(upload_id, 'failed', error_message=str(e))
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute upload: {str(e)}"
        )

@router.get("/pending/ready")
async def get_ready_uploads():
    """
    Get all uploads that are ready to execute (scheduled time has passed).
    
    This endpoint is called by the GitHub Actions worker to get the list of uploads to execute.
    """
    try:
        from app.database import get_pending_uploads_to_execute
        uploads = get_pending_uploads_to_execute()
        return JSONResponse(content={
            "success": True,
            "count": len(uploads),
            "uploads": uploads
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ready uploads: {str(e)}"
        )
