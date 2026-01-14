import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Common Settings
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    
    # Global Kill Switch (if needed, or per profile)
    ALLOW_UPLOAD = os.getenv("ALLOW_UPLOAD", "true").lower() == "true"

    def get_profile_config(self, profile_id: str = None):
        """
        Returns a dict of configuration for a specific profile.
        If profile_id is None or empty, it falls back to the ROOT .env vars (backward compatibility).
        If profile_id is provided (e.g., '1', '2'), it looks for PROFILE_1_...
        """
        prefix = ""
        if profile_id:
            prefix = f"PROFILE_{profile_id}_"
        
        # Helper to get env with prefix or fallback to root if profile_id is "default" (simulated by empty prefix logic above if needed)
        # But per requirements, let's look for specific keys.
        
        # If prefix is "PROFILE_1_", we look for "PROFILE_1_UPLOAD_FACEBOOK"
        # If that's not found, we do NOT fallback to root "UPLOAD_FACEBOOK" automatically to avoid confusion, 
        # unless we explicitly want "default" behavior. 
        # Let's implement: Specific Config -> Common Fallback (optional) -> Defaults
        
        def get_val(key, default=None):
            # Try specific profile key first
            val = os.getenv(f"{prefix}{key}")
            if val is not None:
                return val
            # If valid profile_id given but no specific key, do we fall back?
            # User might want to use same FB page for all profiles but different YouTube. 
            # For simplicity: If profile_id is provided, strict lookup. If not, root lookup.
            if not profile_id:
                return os.getenv(key, default)
            return default

        config = {}
        
        # Toggles
        config["ALLOW_UPLOAD"] = get_val("ALLOW_UPLOAD", "true").lower() == "true"
        config["UPLOAD_FACEBOOK"] = get_val("UPLOAD_FACEBOOK", "false").lower() == "true"
        config["UPLOAD_INSTAGRAM"] = get_val("UPLOAD_INSTAGRAM", "false").lower() == "true"
        config["UPLOAD_YOUTUBE"] = get_val("UPLOAD_YOUTUBE", "false").lower() == "true"
        
        # Credentials
        config["FACEBOOK_PAGE_ID"] = get_val("FACEBOOK_PAGE_ID")
        config["FACEBOOK_ACCESS_TOKEN"] = get_val("FACEBOOK_ACCESS_TOKEN")
        config["INSTAGRAM_ACCOUNT_ID"] = get_val("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        
        # YouTube
        # Token files need unique names per profile to avoid conflict
        # Default: youtube_token.json
        # Profile 1: youtube_token_1.json
        suffix = f"_{profile_id}" if profile_id else ""
        config["YOUTUBE_CLIENT_SECRET_FILE"] = get_val("YOUTUBE_CLIENT_SECRET_FILE",  f"client_secret{suffix}.json")
        # Fallback for secret file: usually it's same for all, so maybe check root if specific missing?
        if not os.path.exists(config["YOUTUBE_CLIENT_SECRET_FILE"]) and profile_id:
             # Try common secret file
             config["YOUTUBE_CLIENT_SECRET_FILE"] = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")

        config["YOUTUBE_TOKEN_FILE"] = get_val("YOUTUBE_TOKEN_FILE", f"youtube_token{suffix}.json")
        
        return config

settings = Settings()

print("--- CONFIGURATION LOADED ---")
# Print default config for sanity check
default_conf = settings.get_profile_config(None)
print(f"Global ALLOW_UPLOAD: {settings.ALLOW_UPLOAD}")
print(f"Default Profile Config (Root): {default_conf}")
print("----------------------------")
