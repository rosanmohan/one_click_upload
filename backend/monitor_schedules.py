"""
Real-time scheduler monitor
Shows live status of scheduled uploads
"""
import time
import os
import sys
from datetime import datetime, timezone

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def monitor_schedules():
    from app.database import get_scheduled_uploads, get_pending_uploads_to_execute
    
    try:
        while True:
            clear_screen()
            
            print("=" * 80)
            print(" " * 25 + "🔄 SCHEDULED UPLOADS MONITOR")
            print("=" * 80)
            
            current_time = datetime.now(timezone.utc)
            print(f"\n⏰ Current Time (UTC): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Local Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Get all uploads
            all_uploads = get_scheduled_uploads()
            pending = [u for u in all_uploads if u['status'] == 'pending']
            completed = [u for u in all_uploads if u['status'] == 'completed']
            failed = [u for u in all_uploads if u['status'] == 'failed']
            ready = get_pending_uploads_to_execute()
            
            # Summary
            print(f"\n📊 DATABASE SUMMARY:")
            print(f"   Total: {len(all_uploads)}")
            print(f"   ⏳ Pending: {len(pending)}")
            print(f"   ✅ Completed: {len(completed)}")
            print(f"   ❌ Failed: {len(failed)}")
            print(f"   🚀 Ready to Execute: {len(ready)}")
            
            if pending:
                print(f"\n⏳ PENDING UPLOADS:")
                print("   " + "-" * 76)
                for upload in pending:
                    scheduled_time = datetime.fromisoformat(upload['scheduled_time'].replace('Z', '+00:00'))
                    time_diff = scheduled_time - current_time
                    time_diff_mins = time_diff.total_seconds() / 60
                    
                    print(f"   📝 {upload['title'][:40]}")
                    print(f"      ID: {upload['id'][:16]}...")
                    print(f"      Scheduled: {upload['scheduled_time']}")
                    
                    if time_diff_mins > 0:
                        hours = int(time_diff_mins // 60)
                        mins = int(time_diff_mins % 60)
                        if hours > 0:
                            print(f"      ⏰ In {hours}h {mins}m")
                        else:
                            print(f"      ⏰ In {mins} minutes")
                    else:
                        print(f"      🚀 READY NOW! (overdue by {int(-time_diff_mins)} minutes)")
                    print()
            
            if ready:
                print(f"\n🚀 READY TO EXECUTE NOW:")
                print("   " + "-" * 76)
                for upload in ready:
                    print(f"   ✅ {upload['title']}")
                    print(f"      Profile: {upload['profile_id']}")
                    print(f"      Platforms: Y={upload['upload_youtube']} F={upload['upload_facebook']} I={upload['upload_instagram']}")
                    print()
                
                print(f"   💡 Run: python scheduled_worker.py")
            
            if completed:
                print(f"\n✅ RECENT COMPLETIONS:")
                print("   " + "-" * 76)
                for upload in completed[-3:]:  # Show last 3
                    print(f"   ✅ {upload['title'][:50]}")
                    print(f"      Executed: {upload.get('executed_at', 'N/A')}")
                    print()
            
            if failed:
                print(f"\n❌ FAILED UPLOADS:")
                print("   " + "-" * 76)
                for upload in failed[:3]:  # Show first 3
                    print(f"   ❌ {upload['title'][:50]}")
                    print(f"      Error: {upload.get('error_message', 'Unknown')[:60]}")
                    print()
            
            if not all_uploads:
                print(f"\n📭 NO UPLOADS IN DATABASE")
                print(f"   Schedule an upload from the frontend to see it here!")
            
            print("\n" + "=" * 80)
            print("   Press Ctrl+C to exit | Refreshing every 5 seconds...")
            print("=" * 80)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)

if __name__ == "__main__":
    print("Starting scheduler monitor...")
    print("This will update every 5 seconds")
    time.sleep(2)
    monitor_schedules()
