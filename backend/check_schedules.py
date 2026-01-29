"""Quick diagnostic script to check scheduled uploads status"""
from app.database import get_pending_uploads_to_execute, get_scheduled_uploads
from datetime import datetime, timezone

print("=" * 60)
print("SCHEDULED UPLOADS DIAGNOSTIC")
print("=" * 60)

# Get all uploads
all_uploads = get_scheduled_uploads()
print(f"\nTotal scheduled uploads in database: {len(all_uploads)}")

# Get pending uploads
pending = get_scheduled_uploads(status='pending')
print(f"Pending uploads: {len(pending)}")

# Get uploads that should execute
ready_to_execute = get_pending_uploads_to_execute()
print(f"Ready to execute now: {len(ready_to_execute)}")

print("\n" + "=" * 60)
print("UPLOAD DETAILS:")
print("=" * 60)

current_time = datetime.now(timezone.utc)
print(f"\nCurrent time (UTC): {current_time.isoformat()}")

for upload in all_uploads[-5:]:  # Show last 5
    print(f"\n📅 Upload ID: {upload['id']}")
    print(f"   Title: {upload['title']}")
    print(f"   Status: {upload['status']}")
    print(f"   Scheduled: {upload['scheduled_time']}")
    print(f"   Profile: {upload['profile_id']}")
    if upload.get('error_message'):
        print(f"   ❌ Error: {upload['error_message']}")

print("\n" + "=" * 60)
