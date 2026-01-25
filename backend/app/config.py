import os
import json
from dotenv import load_dotenv

load_dotenv()

class ProfileSettings:
    def __init__(self, profile_id="kids_fun"):
        self.profile_id = profile_id
        self.profile_dir = os.path.join(os.getcwd(), "profiles", profile_id)
        
        # Ensure dir exists (or fallback to root for default)
        if not os.path.exists(self.profile_dir) and profile_id == "kids_fun":
            # Fallback for migration: use root if profile folder empty/missing
            pass

        # Load Global Env Vars (Base)
        self.ALLOW_UPLOAD = os.getenv("ALLOW_UPLOAD", "true").lower() == "true"
        self.BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
        
        # Cloudinary is global usually, or per profile? Let's assume global for now unless requested.
        self.CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
        self.CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

        # --- Profile Specifics ---
        # 1. Toggles (Can be overridden by env vars like KIDS_FUN_UPLOAD_YOUTUBE)
        prefix = profile_id.upper()
        
        self.UPLOAD_FACEBOOK = os.getenv(f"{prefix}_UPLOAD_FACEBOOK", os.getenv("UPLOAD_FACEBOOK", "false")).lower() == "true"
        self.UPLOAD_INSTAGRAM = os.getenv(f"{prefix}_UPLOAD_INSTAGRAM", os.getenv("UPLOAD_INSTAGRAM", "false")).lower() == "true"
        self.UPLOAD_YOUTUBE = os.getenv(f"{prefix}_UPLOAD_YOUTUBE", os.getenv("UPLOAD_YOUTUBE", "false")).lower() == "true"

        # 2. Credentials
        self.FACEBOOK_PAGE_ID = os.getenv(f"{prefix}_FACEBOOK_PAGE_ID", os.getenv("FACEBOOK_PAGE_ID"))
        self.FACEBOOK_ACCESS_TOKEN = os.getenv(f"{prefix}_FACEBOOK_ACCESS_TOKEN", os.getenv("FACEBOOK_ACCESS_TOKEN"))
        self.INSTAGRAM_ACCOUNT_ID = os.getenv(f"{prefix}_INSTAGRAM_BUSINESS_ACCOUNT_ID", os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"))

        # 3. Files (YouTube)
        # Priority: 
        #   1. Env Var specific to profile (KIDS_FUN_YOUTUBE_TOKEN_FILE)
        #   2. File in profiles/{id}/youtube_token.json
        #   3. Global Env Var (YOUTUBE_TOKEN_FILE) - fallback for default profile
        
        default_token_path = os.path.join(self.profile_dir, "youtube_token.json")
        default_secret_path = os.path.join(self.profile_dir, "client_secret.json")

        self.YOUTUBE_TOKEN_FILE = os.getenv(f"{prefix}_YOUTUBE_TOKEN_FILE", 
                                            default_token_path if os.path.exists(default_token_path) else os.getenv("YOUTUBE_TOKEN_FILE", "youtube_token.json"))
                                            
        self.YOUTUBE_CLIENT_SECRET_FILE = os.getenv(f"{prefix}_YOUTUBE_CLIENT_SECRET_FILE", 
                                                    default_secret_path if os.path.exists(default_secret_path) else os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json"))

def get_settings(profile_id: str = "kids_fun"):
    return ProfileSettings(profile_id)

# Default for backward compatibility (legacy imports)
settings = get_settings("kids_fun")

print("--- CONFIGURATION LOADED (Default: kids_fun) ---")
print(f"ALLOW_UPLOAD: {settings.ALLOW_UPLOAD}")
print(f"UPLOAD_YOUTUBE: {settings.UPLOAD_YOUTUBE} (File: {settings.YOUTUBE_TOKEN_FILE})")
print("----------------------------")
