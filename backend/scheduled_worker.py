"""
Worker script to execute scheduled uploads.
This script is designed to run periodically via GitHub Actions.
"""
# -*- coding: utf-8 -*-
import sys

# Reconfigure stdout for UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import os
from datetime import datetime, timezone
from app.database import get_pending_uploads_to_execute, update_upload_status
from app.config import get_settings
from app.services.youtube_service import upload_to_youtube
from app.services.facebook_service import upload_to_facebook
from app.services.instagram_service import upload_to_instagram

def safe_print(message: str):
    """Safely print messages with emojis, handling Windows encoding issues."""
    try:
        safe_print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        ascii_message = message.encode('ascii', 'replace').decode('ascii')
        safe_print(ascii_message)

def execute_scheduled_uploads():
    """Main worker function to process pending scheduled uploads."""
    
    safe_print(f"🔄 Scheduled Upload Worker Started at {datetime.now(timezone.utc).isoformat()}")
    safe_print("=" * 60)
    
    # Get all pending uploads
    pending_uploads = get_pending_uploads_to_execute()
    
    if not pending_uploads:
        safe_print("✅ No pending uploads to process.")
        return
    
    safe_print(f"📋 Found {len(pending_uploads)} pending upload(s) to process.\n")
    
    for upload in pending_uploads:
        upload_id = upload['id']
        profile_id = upload['profile_id']
        title = upload['title']
        description = upload['description']
        hashtags = upload['hashtags']
        video_path = upload['video_path']
        merge_videos_flag = upload.get('merge_videos', 0)
        
        safe_print(f"🎬 Processing Upload: {upload_id}")
        safe_print(f"   Profile: {profile_id}")
        safe_print(f"   Title: {title}")
        safe_print(f"   Scheduled: {upload['scheduled_time']}")
        safe_print(f"   Video: {video_path}")
        
        # Check if video_path contains JSON (multiple files)
        import json
        video_files = []
        merged_video_path = None
        
        try:
            # Try to parse as JSON (multiple files)
            video_files = json.loads(video_path)
            safe_print(f"   📁 Multiple files detected: {len(video_files)} videos")
            
            # Verify all files exist
            for vf in video_files:
                if not os.path.exists(vf):
                    error_msg = f"Video file not found: {vf}"
                    safe_print(f"   ❌ Error: {error_msg}")
                    update_upload_status(upload_id, 'failed', error_message=error_msg)
                    continue
            
            # Merge videos if merge_videos flag is True
            if merge_videos_flag:
                safe_print(f"   🔄 Merging {len(video_files)} videos...")
                try:
                    from app.services.video_processing_service import merge_videos
                    merged_video_path = merge_videos(video_files)
                    safe_print(f"   ✅ Videos merged: {merged_video_path}")
                    # Use merged video for upload
                    video_path = merged_video_path
                except Exception as e:
                    error_msg = f"Failed to merge videos: {str(e)}"
                    safe_print(f"   ❌ Error: {error_msg}")
                    update_upload_status(upload_id, 'failed', error_message=error_msg)
                    continue
            else:
                # If not merging, use first video
                safe_print(f"   ℹ️ Using first video (merge not enabled)")
                video_path = video_files[0]
                
        except (json.JSONDecodeError, TypeError):
            # Single file path (not JSON)
            video_files = [video_path]
            safe_print(f"   📄 Single file")
        
        # Check if final video file exists
        if not os.path.exists(video_path):
            error_msg = f"Video file not found: {video_path}"
            safe_print(f"   ❌ Error: {error_msg}")
            update_upload_status(upload_id, 'failed', error_message=error_msg)
            # Clean up any merged file
            if merged_video_path and os.path.exists(merged_video_path):
                os.remove(merged_video_path)
            continue
        
        # Load profile settings
        try:
            settings = get_settings(profile_id)
        except Exception as e:
            error_msg = f"Failed to load profile settings: {str(e)}"
            safe_print(f"   ❌ Error: {error_msg}")
            update_upload_status(upload_id, 'failed', error_message=error_msg)
            # Clean up any merged file
            if merged_video_path and os.path.exists(merged_video_path):
                os.remove(merged_video_path)
            continue
        
        # Track upload results
        results = {
            'youtube': None,
            'facebook': None,
            'instagram': None
        }
        errors = []
        
        # YouTube Upload
        if upload['upload_youtube'] and settings.UPLOAD_YOUTUBE:
            try:
                safe_print(f"   📺 Uploading to YouTube...")
                youtube_result = upload_to_youtube(
                    video_path=video_path,
                    title=title,
                    description=f"{description}\n\n{hashtags}",
                    settings=settings
                )
                results['youtube'] = youtube_result.get('id') if youtube_result else None
                safe_print(f"   ✅ YouTube: {results['youtube']}")
            except Exception as e:
                error_msg = f"YouTube upload failed: {str(e)}"
                safe_print(f"   ❌ YouTube Error: {error_msg}")
                errors.append(error_msg)
        
        # Facebook Upload
        if upload['upload_facebook'] and settings.UPLOAD_FACEBOOK:
            try:
                safe_print(f"   📘 Uploading to Facebook...")
                facebook_result = upload_to_facebook(
                    video_path=video_path,
                    description=f"{title}\n\n{description}\n\n{hashtags}",
                    settings=settings
                )
                results['facebook'] = facebook_result.get('id') if facebook_result else None
                safe_print(f"   ✅ Facebook: {results['facebook']}")
            except Exception as e:
                error_msg = f"Facebook upload failed: {str(e)}"
                safe_print(f"   ❌ Facebook Error: {error_msg}")
                errors.append(error_msg)
        
        # Instagram Upload
        if upload['upload_instagram'] and settings.UPLOAD_INSTAGRAM:
            try:
                safe_print(f"   📸 Uploading to Instagram...")
                instagram_result = upload_to_instagram(
                    video_path=video_path,
                    caption=f"{title}\n\n{description}\n\n{hashtags}",
                    settings=settings
                )
                results['instagram'] = instagram_result.get('id') if instagram_result else None
                safe_print(f"   ✅ Instagram: {results['instagram']}")
            except Exception as e:
                error_msg = f"Instagram upload failed: {str(e)}"
                safe_print(f"   ❌ Instagram Error: {error_msg}")
                errors.append(error_msg)
        
        # Update status based on results
        if errors and not any(results.values()):
            # All uploads failed
            status = 'failed'
            error_message = "; ".join(errors)
            safe_print(f"   ❌ Upload FAILED: {error_message}")
        elif errors:
            # Partial success
            status = 'completed'
            error_message = f"Partial success. Errors: {'; '.join(errors)}"
            safe_print(f"   ⚠️ Upload PARTIALLY COMPLETED: {error_message}")
        else:
            # All successful
            status = 'completed'
            error_message = None
            safe_print(f"   ✅ Upload COMPLETED successfully!")
        
        # Update database
        update_upload_status(
            upload_id=upload_id,
            status=status,
            error_message=error_message,
            youtube_video_id=results['youtube'],
            facebook_post_id=results['facebook'],
            instagram_media_id=results['instagram']
        )
        
        # Clean up video files after successful upload
        if status == 'completed':
            try:
                # Clean up the final video file (uploaded one)
                if os.path.exists(video_path):
                    os.remove(video_path)
                    safe_print(f"   🗑️ Cleaned up uploaded video file")
                
                # Clean up individual part files if they were merged
                if merged_video_path and len(video_files) > 1:
                    for vf in video_files:
                        if os.path.exists(vf):
                            os.remove(vf)
                    safe_print(f"   🗑️ Cleaned up {len(video_files)} individual video parts")
                    
            except Exception as e:
                safe_print(f"   ⚠️ Could not delete video files: {str(e)}")
        
        safe_print()  # Blank line for readability
    
    safe_print("=" * 60)
    safe_print(f"✅ Worker Completed at {datetime.now(timezone.utc).isoformat()}")

if __name__ == "__main__":
    try:
        execute_scheduled_uploads()
    except Exception as e:
        safe_print(f"❌ Worker failed with error: {str(e)}")
        sys.exit(1)
