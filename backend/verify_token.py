import requests
import json

# Your new token
ACCESS_TOKEN = "EAASW7vdZAtc0BQoZB1AwAFvd3WYKZB9ZBv7C06Nh6cpwpBPSW4WOkqvnVHnamqpRJSCwCbeZCmfi1ZAKfaHOwKkYOixdYan6yXJkE2nn2oNVlKtELQ0cz8ks3jrzfkFO6akmNMkfqowVpBWDFM3s6AzLyIJKCJIPmFyvb0roDacYYV2AxE5nFIOj9goIE9kAZDZD"

print("=" * 60)
print("TOKEN VERIFICATION TOOL")
print("=" * 60)

# 1. Check token info
print("\n1. Checking token info...")
response = requests.get(
    "https://graph.facebook.com/v18.0/debug_token",
    params={
        "input_token": ACCESS_TOKEN,
        "access_token": ACCESS_TOKEN
    }
)

if response.status_code == 200:
    token_info = response.json()
    print(json.dumps(token_info, indent=2))
    
    if 'data' in token_info:
        data = token_info['data']
        print(f"\n[OK] Token is valid: {data.get('is_valid')}")
        print(f"[OK] Token type: {data.get('type')}")
        print(f"[OK] App ID: {data.get('app_id')}")
        
        if 'expires_at' in data:
            from datetime import datetime
            expiry = datetime.fromtimestamp(data['expires_at'])
            print(f"[OK] Expires at: {expiry}")
        else:
            print(f"[OK] Expires: Never (Long-lived page token)")
        
        if 'scopes' in data:
            print(f"[OK] Permissions: {', '.join(data['scopes'])}")
else:
    print(f"[ERROR] Error: {response.status_code}")
    print(response.text)

# 2. Check which page this token belongs to
print("\n2. Checking associated page...")
response = requests.get(
    "https://graph.facebook.com/v18.0/me",
    params={
        "access_token": ACCESS_TOKEN,
        "fields": "id,name"
    }
)

if response.status_code == 200:
    page_info = response.json()
    print(f"[OK] Page ID: {page_info.get('id')}")
    print(f"[OK] Page Name: {page_info.get('name')}")
else:
    print(f"[ERROR] Error: {response.status_code}")
    print(response.text)

# 3. Check permissions
print("\n3. Checking permissions...")
response = requests.get(
    "https://graph.facebook.com/v18.0/me/permissions",
    params={"access_token": ACCESS_TOKEN}
)

if response.status_code == 200:
    perms = response.json()
    granted = [p['permission'] for p in perms.get('data', []) if p['status'] == 'granted']
    print(f"[OK] Granted permissions: {', '.join(granted)}")
    
    required = ['pages_manage_posts', 'instagram_content_publish']
    missing = [p for p in required if p not in granted]
    if missing:
        print(f"\n[WARNING] Missing required permissions: {', '.join(missing)}")
    else:
        print(f"\n[SUCCESS] All required permissions granted!")
else:
    print(f"[ERROR] Error: {response.status_code}")
    print(response.text)

print("\n" + "=" * 60)
