"""
Complete diagnostic test for scheduled uploads feature
This will test every component and show detailed logs
"""
import os
import sys
from datetime import datetime, timezone, timedelta

print("=" * 80)
print("SCHEDULED UPLOADS - COMPLETE DIAGNOSTIC TEST")
print("=" * 80)

# Test 1: Check if database module works
print("\n[TEST 1] Testing database module...")
try:
    from app.database import (
        init_database,
        create_scheduled_upload,
        get_scheduled_uploads,
        get_pending_uploads_to_execute,
        get_upload_by_id
    )
    print("✅ Database module imported successfully")
except Exception as e:
    print(f"❌ ERROR importing database: {e}")
    sys.exit(1)

# Test 2: Check database location
print("\n[TEST 2] Checking database location...")
from app.database import DATABASE_PATH
print(f"   Database path: {DATABASE_PATH}")
if os.path.exists(DATABASE_PATH):
    size = os.path.getsize(DATABASE_PATH)
    print(f"   ✅ Database exists ({size} bytes)")
else:
    print(f"   ⚠️  Database doesn't exist yet (will be created)")

# Test 3: List all uploads
print("\n[TEST 3] Listing all scheduled uploads...")
try:
    all_uploads = get_scheduled_uploads()
    print(f"   Total uploads in database: {len(all_uploads)}")
    
    if all_uploads:
        print("\n   Recent uploads:")
        for upload in all_uploads[-5:]:
            print(f"   - ID: {upload['id'][:8]}...")
            print(f"     Title: {upload['title']}")
            print(f"     Status: {upload['status']}")
            print(f"     Scheduled: {upload['scheduled_time']}")
            print(f"     Created: {upload['created_at']}")
            if upload.get('error_message'):
                print(f"     Error: {upload['error_message']}")
            print()
    else:
        print("   ⚠️  No uploads found in database")
except Exception as e:
    print(f"   ❌ ERROR listing uploads: {e}")

# Test 4: Check pending uploads
print("\n[TEST 4] Checking pending uploads...")
try:
    pending = get_scheduled_uploads(status='pending')
    print(f"   Pending uploads: {len(pending)}")
    
    if pending:
        current_time = datetime.now(timezone.utc)
        print(f"   Current time (UTC): {current_time.isoformat()}")
        print("\n   Pending upload details:")
        for upload in pending:
            scheduled_time = datetime.fromisoformat(upload['scheduled_time'].replace('Z', '+00:00'))
            time_diff = scheduled_time - current_time
            print(f"   - {upload['title']}")
            print(f"     Scheduled: {upload['scheduled_time']}")
            if time_diff.total_seconds() > 0:
                print(f"     ⏰ Scheduled for: {time_diff.total_seconds()/60:.1f} minutes from now")
            else:
                print(f"     ✅ READY TO EXECUTE (overdue by {-time_diff.total_seconds()/60:.1f} minutes)")
            print()
except Exception as e:
    print(f"   ❌ ERROR checking pending: {e}")

# Test 5: Check uploads ready to execute
print("\n[TEST 5] Checking uploads ready to execute NOW...")
try:
    ready = get_pending_uploads_to_execute()
    print(f"   Ready to execute: {len(ready)}")
    
    if ready:
        print("\n   Uploads that should execute now:")
        for upload in ready:
            print(f"   - {upload['title']}")
            print(f"     Video: {upload['video_path']}")
            print(f"     Platforms: YouTube={upload['upload_youtube']}, Facebook={upload['upload_facebook']}, Instagram={upload['upload_instagram']}")
            print()
    else:
        print("   ℹ️  No uploads ready to execute")
except Exception as e:
    print(f"   ❌ ERROR checking ready uploads: {e}")

# Test 6: Create a test upload
print("\n[TEST 6] Creating a test scheduled upload...")
try:
    import uuid
    test_id = str(uuid.uuid4())
    future_time = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    
    # Create a dummy video file for testing
    test_video_dir = os.path.join(os.getcwd(), "scheduled_videos")
    if not os.path.exists(test_video_dir):
        os.makedirs(test_video_dir)
    
    test_video_path = os.path.join(test_video_dir, f"{test_id}_test.mp4")
    with open(test_video_path, 'w') as f:
        f.write("test video content")
    
    result = create_scheduled_upload(
        upload_id=test_id,
        profile_id="kids_fun",
        title="TEST UPLOAD - DELETE ME",
        description="This is a test upload for diagnostics",
        hashtags="#test",
        scheduled_time=future_time,
        video_filename=f"{test_id}_test.mp4",
        video_path=test_video_path,
        merge_videos=False,
        upload_youtube=False,  # Set to False to avoid actual upload
        upload_facebook=False,
        upload_instagram=False
    )
    print(f"   ✅ Test upload created successfully!")
    print(f"   ID: {test_id}")
    print(f"   Scheduled for: {future_time}")
    
    # Verify it was created
    test_upload = get_upload_by_id(test_id)
    if test_upload:
        print(f"   ✅ Verified: Upload found in database")
    else:
        print(f"   ❌ ERROR: Upload not found after creation!")
        
except Exception as e:
    print(f"   ❌ ERROR creating test upload: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Test worker import
print("\n[TEST 7] Testing worker script import...")
try:
    sys.path.insert(0, os.getcwd())
    # Don't actually run it, just test if it can be imported
    import scheduled_worker
    print("   ✅ Worker script can be imported")
except Exception as e:
    print(f"   ❌ ERROR importing worker: {e}")
    import traceback
    traceback.print_exc()

# Test 8: Check environment and settings
print("\n[TEST 8] Checking configuration...")
try:
    from app.config import get_settings
    settings = get_settings("kids_fun")
    print(f"   ✅ Config loaded for profile: kids_fun")
    print(f"   ALLOW_UPLOAD: {settings.ALLOW_UPLOAD}")
    print(f"   UPLOAD_YOUTUBE: {settings.UPLOAD_YOUTUBE}")
    print(f"   UPLOAD_FACEBOOK: {settings.UPLOAD_FACEBOOK}")
    print(f"   UPLOAD_INSTAGRAM: {settings.UPLOAD_INSTAGRAM}")
except Exception as e:
    print(f"   ❌ ERROR loading config: {e}")

# Summary
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

all_uploads_final = get_scheduled_uploads()
pending_final = get_scheduled_uploads(status='pending')
ready_final = get_pending_uploads_to_execute()

print(f"\n📊 Database Status:")
print(f"   Total uploads: {len(all_uploads_final)}")
print(f"   Pending: {len(pending_final)}")
print(f"   Ready to execute: {len(ready_final)}")

if len(ready_final) > 0:
    print(f"\n✅ GOOD NEWS: You have {len(ready_final)} upload(s) ready to execute!")
    print(f"   Run: python scheduled_worker.py")
elif len(pending_final) > 0:
    print(f"\n⏰ WAITING: You have {len(pending_final)} pending upload(s)")
    print(f"   They will be ready after their scheduled time")
else:
    print(f"\n📝 NO UPLOADS: Database is empty or all uploads completed")
    print(f"   Try scheduling a new upload from the frontend")

print("\n" + "=" * 80)
print("To test the worker: python scheduled_worker.py")
print("To clean up test upload: Check scheduled_uploads table")
print("=" * 80)
