# 🧪 Complete Scheduled Uploads Testing Guide

## ❌ Issues Found:

1. **Database is empty** - Your previous uploads didn't save
2. **Uploads are disabled** - `ALLOW_UPLOAD=false` in `.env`

## ✅ Step-by-Step Testing Process

### STEP 1: Enable Uploads (REQUIRED)

Edit `backend/.env` file and change:

```env
ALLOW_UPLOAD=true

# Enable at least one platform for testing
UPLOAD_FACEBOOK=true
# OR
UPLOAD_YOUTUBE=true  
# OR
UPLOAD_INSTAGRAM=true
```

**For testing, enable at least ONE platform!**

---

### STEP 2: Restart Backend Server

```bash
cd backend
# Press Ctrl+C to stop current server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### STEP 3: Schedule a Test Upload (Frontend)

1. **Open frontend:**
   ```
   http://localhost:5173/one_click_upload/
   ```

2. **Activate Server** (should turn green)

3. **Select a video file**

4. **Fill in details:**
   - Title: "Test Scheduled Upload"
   - Description: "Testing"
   - Hashtags: "#test"

5. **✅ Check "Schedule for later?"**

6. **Set time: 2 minutes from now**
   - Example: If it's 7:10 AM, set to 7:12 AM

7. **Click "📅 Schedule Upload"**

8. **Verify success message appears**

9. **Switch to "Scheduled" tab** - you should see your upload with status "Pending"

---

### STEP 4: Verify Database (Backend)

```bash
cd backend
python test_scheduled_uploads.py
```

**Expected output:**
```
Total uploads in database: 1
Pending: 1
Ready to execute: 0  (will be 1 after scheduled time)
```

**If it shows 0 uploads:**
- ❌ Frontend didn't connect to backend
- Check browser console (F12) for errors
- Check backend terminal for incoming requests

---

### STEP 5: Wait for Scheduled Time

Wait until the scheduled time passes (e.g., 7:12 AM passes)

---

### STEP 6: Check if Upload is Ready

```bash
cd backend
python test_scheduled_uploads.py
```

**Expected output:**
```
Ready to execute: 1  ← Should show 1 now!
```

---

### STEP 7: Run Worker Manually (Local Test)

```bash
cd backend
python scheduled_worker.py
```

**Expected logs:**
```
🔄 Scheduled Upload Worker Started
📋 Found 1 pending upload(s) to process

🎬 Processing Upload: [id]
   Profile: kids_fun
   Title: Test Scheduled Upload
   📄 Single file
   📺 Uploading to YouTube... (or Facebook/Instagram)
   ✅ YouTube: [video-id]
   ✅ Upload COMPLETED successfully!
   🗑️ Cleaned up video file

✅ Worker Completed
```

---

### STEP 8: Verify in Frontend

1. **Go to "Scheduled" tab**
2. **Click refresh button** 🔄
3. **Status should change:** "Pending" → "Completed" ✅

---

### STEP 9: Verify on Social Media

1. **Check the platform you enabled:**
   - YouTube: youtube.com/my_videos
   - Facebook: facebook.com/your_page
   - Instagram: instagram.com

2. **You should see your video posted!**

---

## 🔍 Troubleshooting Each Step

### Issue: "Total uploads: 0" after Step 4

**Cause:** Frontend didn't send request to backend

**Debug:**
1. Open browser console (F12)
2. Go to Network tab
3. Try scheduling again
4. Look for POST request to `/api/scheduled/upload`
5. Check if it's:
   - ❌ Red/Failed → Backend error
   - ✅ Green/200 → Success but might be wrong backend

**Fix:**
- Check `frontend/src/App.jsx` line 31:
  ```javascript
  const [apiUrl, setApiUrl] = useState('http://localhost:8000');
  ```
- Make sure backend is running on port 8000

---

### Issue: "ALLOW_UPLOAD: False" in config

**Cause:** `.env` file has uploads disabled

**Fix:**
1. Edit `backend/.env`
2. Change `ALLOW_UPLOAD=false` to `ALLOW_UPLOAD=true`
3. Enable at least one platform (UPLOAD_FACEBOOK, etc.)
4. Restart backend server

---

### Issue: Worker shows "No pending uploads"

**Cause:** Scheduled time hasn't passed yet

**Debug:**
```bash
python test_scheduled_uploads.py
```

Check output:
```
Scheduled for: 2026-01-29T02:00:00
⏰ Scheduled for: 15.5 minutes from now  ← Still in future!
```

**Wait** until time passes, then run worker.

---

### Issue: Worker fails with errors

**Possible Errors:**

1. **"Video file not found"**
   - File was deleted or path is wrong
   - Check `backend/scheduled_videos/` folder

2. **"Failed to load profile settings"**
   - Profile doesn't exist in config
   - Create profile folder: `backend/profiles/kids_fun/`

3. **"Authentication failed" (YouTube/Facebook/Instagram)**
   - API tokens expired
   - Regenerate tokens

---

## 📊 Quick Status Check Command

Run anytime to see status:

```bash
cd backend
python -c "from app.database import get_scheduled_uploads, get_pending_uploads_to_execute; all=get_scheduled_uploads(); pending=get_pending_uploads_to_execute(); print(f'Total: {len(all)}, Pending: {len([u for u in all if u[\"status\"]==\"pending\"])}, Ready: {len(pending)}')"
```

---

## 🎯 Expected Results for Full Test

| Step | Expected Result |
|------|-----------------|
| 1. Enable uploads | `.env` has `ALLOW_UPLOAD=true` |
| 2. Restart server | Server shows "Application startup complete" |
| 3. Schedule upload | Success message + appears in "Scheduled" tab |
| 4. Check database | `Total uploads: 1` |
| 5. Wait for time | Clock passes scheduled time |
| 6. Check ready | `Ready to execute: 1` |
| 7. Run worker | Logs show upload success |
| 8. Check frontend | Status = "Completed" |
| 9. Check platform | Video visible on social media |

---

## ⚡ Quick Test (Skip GitHub Actions)

For **immediate testing** without waiting:

```bash
# 1. Enable uploads in .env
# 2. Restart backend
# 3. Create a very short test video (1-2 seconds)
# 4. Schedule it for 30 seconds from now
# 5. Wait 30 seconds
# 6. Run: python scheduled_worker.py
# 7. Should upload immediately!
```

---

## 📝 Production Testing (GitHub Actions)

Only test GitHub Actions AFTER local testing works:

1. **Commit and push** all changes
2. **Go to GitHub Actions** tab
3. **Check "Scheduled Upload Worker"** runs every 15 min
4. **Manually trigger:** Click "Run workflow"
5. **Check logs** for detailed output

**Note:** GitHub Actions uses its own database (artifacts), separate from local!

---

## 🆘 Still Not Working?

Run the diagnostic and share the output:

```bash
cd backend
python test_scheduled_uploads.py > diagnostic_output.txt
```

Then check `diagnostic_output.txt` for detailed information.

---

## ✅ Success Checklist

- [ ] `.env` has `ALLOW_UPLOAD=true`
- [ ] At least one platform enabled (FACEBOOK/YOUTUBE/INSTAGRAM)
- [ ] Backend server running
- [ ] Frontend loads at localhost:5173
- [ ] Can schedule upload (appears in "Scheduled" tab)
- [ ] Database shows upload (test script)
- [ ] Worker runs without errors
- [ ] Upload status changes to "Completed"
- [ ] Video appears on social media

---

Good luck with testing! 🚀
