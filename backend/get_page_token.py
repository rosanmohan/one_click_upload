import requests
import json

# Your SYSTEM_USER token
SYSTEM_TOKEN = "EAASW7vdZAtc0BQoZB1AwAFvd3WYKZB9ZBv7C06Nh6cpwpBPSW4WOkqvnVHnamqpRJSCwCbeZCmfi1ZAKfaHOwKkYOixdYan6yXJkE2nn2oNVlKtELQ0cz8ks3jrzfkFO6akmNMkfqowVpBWDFM3s6AzLyIJKCJIPmFyvb0roDacYYV2AxE5nFIOj9goIE9kAZDZD"

print("=" * 70)
print("FETCHING AYESHA PAGE ACCESS TOKEN FROM SYSTEM USER")
print("=" * 70)

# Get all pages accessible by this system user
print("\n1. Fetching pages associated with System User...")
response = requests.get(
    "https://graph.facebook.com/v18.0/me/accounts",
    params={"access_token": SYSTEM_TOKEN}
)

if response.status_code == 200:
    data = response.json()
    
    if 'data' in data and len(data['data']) > 0:
        print(f"\n[SUCCESS] Found {len(data['data'])} page(s):\n")
        
        for page in data['data']:
            page_id = page.get('id')
            page_name = page.get('name')
            page_token = page.get('access_token')
            
            print(f"Page Name: {page_name}")
            print(f"Page ID: {page_id}")
            
            # Check if this is the Ayesha page
            if page_id == "1003802406139088" or "ayesha" in page_name.lower():
                print(f"\n{'='*70}")
                print(f"[AYESHA PAGE FOUND!]")
                print(f"{'='*70}")
                print(f"\nPage Name: {page_name}")
                print(f"Page ID: {page_id}")
                print(f"\n** NEVER-EXPIRING PAGE ACCESS TOKEN **")
                print(f"{page_token}")
                print(f"\n{'='*70}")
                
                # Verify this token
                verify_response = requests.get(
                    "https://graph.facebook.com/v18.0/debug_token",
                    params={
                        "input_token": page_token,
                        "access_token": SYSTEM_TOKEN
                    }
                )
                
                if verify_response.status_code == 200:
                    token_data = verify_response.json().get('data', {})
                    print(f"\n[TOKEN VERIFICATION]")
                    print(f"Type: {token_data.get('type')}")
                    print(f"Expires: {token_data.get('expires_at', 'Never (0 = never)')}")
                    print(f"Valid: {token_data.get('is_valid')}")
                    
                    if token_data.get('scopes'):
                        print(f"\nPermissions:")
                        for scope in token_data.get('scopes', []):
                            print(f"  - {scope}")
                
                print(f"\n{'='*70}")
                print(f"UPDATE THIS TOKEN ON RENDER:")
                print(f"AYESHA_FACEBOOK_ACCESS_TOKEN={page_token}")
                print(f"{'='*70}\n")
            else:
                print(f"Access Token: {page_token[:20]}...")
                print("-" * 50)
    else:
        print("\n[ERROR] No pages found. The System User might not have access to pages.")
        print("You need to assign the Ayesha page to the System User in Business Settings.")
else:
    print(f"\n[ERROR] Failed to fetch pages: {response.status_code}")
    print(response.text)

print("\n" + "=" * 70)
