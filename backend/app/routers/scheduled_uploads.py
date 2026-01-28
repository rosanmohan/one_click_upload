from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
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
        if scheduled_dt <= datetime.utcnow():
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
    
    # Save video file(s)
    saved_files = []
    try:
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
    except Exception as e:
        # Clean up any saved files on error
        for saved_path in saved_files:
            if os.path.exists(saved_path):
                os.remove(saved_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save video file: {str(e)}"
        )
    
    # Store multiple file paths as JSON if multiple files, otherwise single path
    # The worker script will handle merging if merge_videos is True
    import json
    if len(saved_files) == 1:
        final_video_path = saved_files[0]
        final_video_filename = os.path.basename(final_video_path)
    else:
        # Store all paths as JSON - worker will merge them
        final_video_path = json.dumps(saved_files)
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
