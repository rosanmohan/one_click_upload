# Testing Production Deployment - Scheduled Uploads

## 📍 Your Deployed URLs

Before testing, you need to find your actual deployed URLs:

### 1. Backend URL (Render)
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Find your service (e.g., "one-click-backend")
3. Copy the URL (looks like: `https://your-service-name.onrender.com`)

### 2. Frontend URL (GitHub Pages)
Your frontend should be deployed at:
```
https://<your-github-username>.github.io/one_click_upload/
```

To find it:
1. Go to your GitHub repository
2. Click **Settings** → **Pages**
3. You'll see: "Your site is live at https://..."

---

## ✅ Pre-Test Checklist

Before testing, ensure you've completed these steps:

### GitHub Secrets (for Scheduled Worker)
Go to GitHub → Settings → Secrets and variables → Actions

Verify you have these secrets set:

#### Global Settings
- [ ] `ALLOW_UPLOAD` = `true`

#### Kids Fun Profile
- [ ] `UPLOAD_FACEBOOK` = `true`
- [ ] `UPLOAD_INSTAGRAM` = `true`
- [ ] `UPLOAD_YOUTUBE` = `true`
- [ ] `FACEBOOK_PAGE_ID`
- [ ] `FACEBOOK_ACCESS_TOKEN`
- [ ] `INSTAGRAM_BUSINESS_ACCOUNT_ID`

#### Ayesha Profile (if using)
- [ ] `AYESHA_UPLOAD_FACEBOOK` = `true`
- [ ] `AYESHA_UPLOAD_INSTAGRAM` = `true`
- [ ] `AYESHA_UPLOAD_YOUTUBE` = `true`
- [ ] `AYESHA_FACEBOOK_PAGE_ID`
- [ ] `AYESHA_FACEBOOK_ACCESS_TOKEN`
- [ ] `AYESHA_INSTAGRAM_BUSINESS_ACCOUNT_ID`

#### Cloudinary
- [ ] `CLOUDINARY_CLOUD_NAME`
- [ ] `CLOUDINARY_API_KEY`
- [ ] `CLOUDINARY_API_SECRET`

#### Frontend Deployment
- [ ] `VITE_API_URL` = Your Render backend URL (e.g., `https://your-service.onrender.com`)

---

## 🧪 Testing the Deployed Application

### Test 1: Verify Deployment

1. **Open your frontend URL** in a browser:
   ```
   https://<your-username>.github.io/one_click_upload/
   ```

2. **Check the server activation:**
   - Click "Activate Server"
   - It should turn from red → blue (activating) → green (connected)
   - If it stays red, check:
     - Is your Render backend URL correct in `VITE_API_URL`?
     - Is your Render backend service running?
     - Check browser console (F12) for errors

3. **Verify backend is accessible:**
   Open in a new tab:
   ```
   https://your-service.onrender.com/health
   ```
   You should see: `{"status":"ok"}`

---

### Test 2: Immediate Upload (Optional)

Before testing scheduled uploads, verify the basic upload works:

1. Select a short test video (< 1 minute)
2. Choose profile (kids_fun or ayesha)
3. Fill in title, description, hashtags
4. **Do NOT check "Schedule for later?"**
5. Click "🚀 Upload Now"
6. Wait for upload to complete
7. Check your social media accounts to confirm

---

### Test 3: Schedule an Upload

Now test the scheduled upload feature:

1. **Navigate to your frontend**
2. Click "Activate Server" (wait for green)
3. **Select a test video**
4. **Fill in details:**
   - Title: "Test Scheduled Upload"
   - Description: "Testing the scheduled upload feature"
   - Hashtags: "#test"
5. **✅ Check "Schedule for later?"**
6. **Set the time:**
   - Pick a time **30 minutes from now** (to give you time to verify)
   - Example: If it's 8:00 AM now, set it to 8:30 AM
7. **Click "📅 Schedule Upload"**
8. **Success!** You should see:
   - Alert: "Upload scheduled successfully for [time]"
   - Page switches to "Scheduled" view
   - Your upload appears with status "Pending"

---

### Test 4: Verify GitHub Actions Worker

The GitHub Actions worker runs every 15 minutes and checks for pending uploads.

1. **Go to your GitHub repository**
2. Click **Actions** tab
3. Find **"Scheduled Upload Worker"** workflow
4. You should see it running automatically every 15 minutes

**Manual Trigger (for testing):**
1. Click on "Scheduled Upload Worker"
2. Click **"Run workflow"** dropdown
3. Click **"Run workflow"** button
4. Wait 1-2 minutes
5. Click on the running workflow to see logs

**What to look for in logs:**
```
🔄 Scheduled Upload Worker Started at [timestamp]
============================================================
📋 Found 1 pending upload(s) to process.

🎬 Processing Upload: [upload-id]
   Profile: kids_fun
   Title: Test Scheduled Upload
   Scheduled: [your-scheduled-time]
   Video: [path]
   📺 Uploading to YouTube...
   ✅ YouTube: [video-id]
   📘 Uploading to Facebook...
   ✅ Facebook: [post-id]
   📸 Uploading to Instagram...
   ✅ Instagram: [media-id]
   ✅ Upload COMPLETED successfully!
============================================================
✅ Worker Completed at [timestamp]
```

---

### Test 5: Verify Upload Completed

After the worker runs (either manually or at scheduled time):

1. **Go back to your frontend**
2. Click **"Scheduled"** tab
3. Click the **refresh icon** 🔄
4. Your upload should now show **"Completed"** status ✅
5. **Check your social media accounts** to verify the video was posted

---

## 🔍 Troubleshooting

### Frontend Won't Activate (Stays Red)

**Problem:** "Activate Server" button stays red or shows error.

**Solutions:**
1. Check browser console (F12) for errors
2. Verify `VITE_API_URL` secret in GitHub is correct
3. Test backend directly: `https://your-service.onrender.com/health`
4. Render free tier: Backend "spins down" after inactivity. First request may take 30-60 seconds to wake up. Try again.

### Scheduled Upload Not Executing

**Problem:** Upload stays "Pending" even after scheduled time passes.

**Solutions:**
1. **Check GitHub Actions:**
   - Go to Actions tab
   - Look for "Scheduled Upload Worker" runs
   - Check logs for errors
2. **Check secrets:** All required secrets must be set
3. **Manual trigger:** Run workflow manually to test immediately
4. **Check scheduled time:** Must be in the future when created

### Worker Fails with Errors

**Problem:** GitHub Actions logs show errors.

**Common Errors:**

1. **"ModuleNotFoundError"**
   - Solution: Check `requirements.txt` in backend folder
   - Ensure all dependencies are listed

2. **"Authentication failed" (Facebook/Instagram/YouTube)**
   - Solution: 
     - Facebook: Access token may have expired (regenerate)
     - YouTube: Token files not accessible (GitHub Actions can't access them)
     - For YouTube: You may need to disable YouTube uploads in production for now

3. **"Database not found"**
   - Solution: Worker downloads database from artifacts
   - First run: Database is created automatically
   - Subsequent runs: Database persists via artifacts

### YouTube Not Working in Production

**Problem:** YouTube uploads work locally but fail in GitHub Actions.

**Reason:** GitHub Actions can't access your local `youtube_token.json` file.

**Solutions:**
1. **Short-term:** Disable YouTube uploads in production
   ```
   UPLOAD_YOUTUBE=false
   AYESHA_UPLOAD_YOUTUBE=false
   ```

2. **Long-term:** 
   - Create OAuth2 service account (more complex)
   - Use GitHub's large file storage
   - Or deploy backend to Render where you can upload the token file

---

## 📊 Expected Timeline

Here's what happens after you schedule an upload:

```
Time: 8:00 AM - You schedule upload for 8:30 AM
Time: 8:15 AM - GitHub Actions runs (checks database, finds upload scheduled for 8:30 AM, does nothing)
Time: 8:30 AM - Scheduled time passes
Time: 8:30-8:45 AM - Worker runs at next interval (8:45 AM), finds upload is due, executes it
Time: 8:45 AM - Status changes to "Completed" ✅
```

**Key Point:** Worker runs every 15 minutes, so there can be up to a 15-minute delay after the scheduled time.

---

## 🎯 Quick Test Command

To quickly verify everything is working, open browser console (F12) and run:

```javascript
// Test backend connection
fetch('https://your-service.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log('Backend:', d))
  .catch(e => console.error('Backend Error:', e));

// Test scheduled uploads API
fetch('https://your-service.onrender.com/api/scheduled/list')
  .then(r => r.json())
  .then(d => console.log('Scheduled Uploads:', d))
  .catch(e => console.error('API Error:', e));
```

Replace `your-service.onrender.com` with your actual backend URL.

---

## ✅ Success Checklist

- [ ] Frontend loads at GitHub Pages URL
- [ ] "Activate Server" button turns green
- [ ] Can view "Scheduled" tab
- [ ] Can schedule an upload
- [ ] Upload appears in "Scheduled" list with "Pending" status
- [ ] GitHub Actions workflow runs successfully
- [ ] Upload status changes to "Completed" after execution
- [ ] Video appears on social media platforms

---

## 📝 Notes

1. **Render Free Tier:** Backend may "spin down" after 15 minutes of inactivity. First request may be slow (30-60s).

2. **GitHub Actions Limits:** 
   - Free tier: 2000 minutes/month
   - Running every 15 minutes = 96 runs/day = ~2880 runs/month
   - Each run takes ~1-2 minutes
   - Total usage: ~2880-5760 minutes/month (may exceed free tier if uploading large videos)

3. **Database Persistence:** 
   - SQLite database is stored in GitHub Actions artifacts
   - Artifacts expire after 90 days by default
   - Plan accordingly for long-term storage

4. **Video Files:**
   - Stored in `backend/scheduled_videos/` directory
   - On Render: Files are ephemeral (lost on restart)
   - On GitHub Actions: Downloaded from artifacts, processed, then cleaned up

---

## 🚀 Ready to Test!

You now have everything you need to test your deployed scheduled upload feature. Start with **Test 1** and work your way through. Good luck! 🎉
