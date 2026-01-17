import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ALLOW_UPLOAD = os.getenv("ALLOW_UPLOAD", "true").lower() == "true"
    UPLOAD_FACEBOOK = os.getenv("UPLOAD_FACEBOOK", "false").lower() == "true"
    UPLOAD_INSTAGRAM = os.getenv("UPLOAD_INSTAGRAM", "false").lower() == "true"
    UPLOAD_YOUTUBE = os.getenv("UPLOAD_YOUTUBE", "false").lower() == "true"

    FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
    FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
    INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    
    # Path to client_secret.json and youtube_token.json
    YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")
    YOUTUBE_TOKEN_FILE = os.getenv("YOUTUBE_TOKEN_FILE", "youtube_token.json")
    
    # Base URL for serving static files (needed if not using Cloudinary)
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

settings = Settings()

print("--- CONFIGURATION LOADED ---")
print(f"ALLOW_UPLOAD: {settings.ALLOW_UPLOAD}")
print(f"UPLOAD_FACEBOOK: {settings.UPLOAD_FACEBOOK}")
print(f"UPLOAD_INSTAGRAM: {settings.UPLOAD_INSTAGRAM}")
print(f"UPLOAD_YOUTUBE: {settings.UPLOAD_YOUTUBE}")
print("----------------------------")
