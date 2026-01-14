import cloudinary
import cloudinary.uploader
from app.config import settings

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

def upload_video_to_cloudinary(file_path):
    """
    Uploads a video to Cloudinary and returns the secure URL and public_id.
    """
    if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
        print("Cloudinary credentials missing.")
        return None

    try:
        print(f"Uploading to Cloudinary: {file_path}")
        response = cloudinary.uploader.upload(
            file_path, 
            resource_type="video",
            folder="one_click_social_upload"
        )
        print(f"Cloudinary Upload Success: {response.get('secure_url')}")
        return {
            "url": response.get("secure_url"),
            "public_id": response.get("public_id")
        }
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None

def delete_video_from_cloudinary(public_id):
    """
    Deletes a video from Cloudinary using its public_id.
    """
    if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
        return None

    try:
        cloudinary.uploader.destroy(public_id, resource_type="video")
        return True
    except Exception as e:
        print(f"Cloudinary delete failed: {e}")
        return False
