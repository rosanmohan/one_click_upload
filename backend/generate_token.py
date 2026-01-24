import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Scopes needed for upload
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'youtube_token.json'

def main():
    print("--- YouTube Token Generator ---")
    
    # Check if client_secret.json exists
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Error: '{CLIENT_SECRET_FILE}' not found in the current directory.")
        print("Please download your OAuth 2.0 Client Secret JSON from Google Cloud Console.")
        print("Rename it to 'client_secret.json' and place it in this folder.")
        return

    print("Starting OAuth flow...")
    print("A browser window will open. Please log in with your YouTube Google Account.")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, SCOPES)
    
    # Run the local server to let the user auth
    creds = flow.run_local_server(port=0)
    
    print("\nAuthentication successful!")
    
    # Save the credentials
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
        
    print(f"Token saved to '{TOKEN_FILE}'.")
    print("\nIMPORTANT: To prevent this token from expiring in 7 days:")
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Navigate to 'APIs & Services' > 'OAuth consent screen'")
    print("3. Under 'Publishing status', click 'PUBLISH APP' to set it to 'In production'.")
    print("   (You don't need to verify the app, just set to production)")
    
if __name__ == '__main__':
    main()
