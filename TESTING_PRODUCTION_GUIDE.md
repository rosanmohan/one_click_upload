# 🌐 Testing Scheduled Uploads in Production (Deployed Environment)

## 📍 Step 1: Find Your Deployed URLs

### Frontend (GitHub Pages)
Your app is deployed at:
```
https://rosanmohan.github.io/one_click_upload/
```

**To verify:**
1. Go to: https://github.com/rosanmohan/one_click_upload
2. Click **Settings** → **Pages** (left sidebar)
3. You'll see: "Your site is live at https://..."

### Backend (Render)
You should have deployed the backend to Render.

**To find your backend URL:**
1. Go to: https://dashboard.render.com/
2. Find your service (probably named "one-click-backend" or similar)
3. Copy the URL (looks like: `https://your-service-name.onrender.com`)

**Test backend health:**
```
https://your-backend-url.onrender.com/health
```
Should return: `{"status":"ok"}`

---

## ⚙️ Step 2: Verify GitHub Secrets

Go to: https://github.com/rosanmohan/one_click_upload/settings/secrets/actions

**Check you have these secrets set:**

### Required Secrets:
- [ ] `VITE_API_URL` = Your Render backend URL
- [ ] `ALLOW_UPLOAD` = `true`
- [ ] `UPLOAD_FACEBOOK` = `true` (or whichever platform you want)
- [ ] `FACEBOOK_PAGE_ID` = Your page ID
- [ ] `FACEBOOK_ACCESS_TOKEN` = Your token
- [ ] `INSTAGRAM_BUSINESS_ACCOUNT_ID` = Your account ID
- [ ] `CLOUDINARY_CLOUD_NAME` = Your Cloudinary name
- [ ] `CLOUDINARY_API_KEY` = Your API key
- [ ] `CLOUDINARY_API_SECRET` = Your API secret

**If any are missing, add them:**
1. Click "New repository secret"
2. Enter name and value
3. Click "Add secret"

---

## 🧪 Step 3: Test Frontend-Backend Connection

### 3.1 Open Deployed Frontend
```
https://rosanmohan.github.io/one_click_upload/
```

### 3.2 Activate Server
1. Click **"Activate Server"** button
2. Wait for it to load
3. **Expected:** Button turns GREEN ✅

**If it stays RED:**
- ❌ Backend is down or URL is wrong
- Check `VITE_API_URL` secret in GitHub
- Check Render backend is running
- Check browser console (F12) for errors

### 3.3 Check Browser Console
Press **F12** → **Console** tab

Look for:
```
Server activated successfully!
```

**If you see errors:**
- `Failed to fetch` = Backend not accessible
- `CORS error` = Backend CORS misconfigured
- `Network error` = Backend URL wrong

---

## 📅 Step 4: Schedule a Test Upload

### 4.1 Prepare Test Video
- **Use a VERY SHORT video** (5-10 seconds max)
- Smaller file size = faster testing
- MP4 format recommended

### 4.2 Fill Upload Form
1. **Select Profile:** Choose "kids_fun" or "ayesha"
2. **Upload Video:** Click and select your short test video
3. **Title:** "Test Scheduled Upload"
4. **Description:** "Testing production deployment"
5. **Hashtags:** Select or type "#test"

### 4.3 Schedule It
1. ✅ **Check "Schedule for later?"**
2. **Set time:** 15 minutes from now
   - Example: If it's 7:30 AM, set to 7:45 AM
   - **Important:** Use your local timezone, it will be converted
3. **Click "📅 Schedule Upload"**

### 4.4 Verify Success
**Expected:**
- ✅ Success message appears
- ✅ Automatically switches to "Scheduled" tab
- ✅ Your upload appears in the list with status "Pending"

**If it fails:**
- Check browser console for error
- Check browser Network tab (F12 → Network)
- Look for POST to `/api/scheduled/upload`
- Click on it to see response

---

## 🔍 Step 5: Verify Upload Was Saved

### 5.1 Check Scheduled Tab
1. Click **"Scheduled"** tab in the app
2. You should see your upload listed
3. **Status:** Should show "Pending" ⏳
4. **Note the Upload ID** (first few characters)

### 5.2 Refresh to Confirm
1. Click the refresh icon 🔄
2. Upload should still be there
3. Status still "Pending"

**If upload disappeared:**
- ❌ Didn't save to database
- Backend may have crashed
- Check Render logs

---

## ⚠️ IMPORTANT: Architecture Issue

### Current Problem:
```
┌─────────────────────────┐
│ GitHub Pages (Frontend) │
└───────────┬─────────────┘
            ↓
┌───────────────────────────┐
│ Render Backend            │
│ - API endpoints work      │
│ - Saves to SQLite DB      │
│ - DB is on Render server  │
└───────────────────────────┘

┌───────────────────────────┐
│ GitHub Actions Worker     │
│ - Has separate DB         │
│ - CANNOT access Render DB │  ❌ PROBLEM!
│ - Won't find your upload  │
└───────────────────────────┘
```

### What This Means:
- ✅ **Scheduling works** - your upload saves to Render's database
- ❌ **Worker won't execute** - GitHub Actions can't access Render's database
- **They're isolated from each other!**

---

## ✅ Step 6: What You CAN Test Now

### Test 1: Frontend Scheduling
1. Schedule upload (Steps 4.1-4.4)
2. Verify it appears in "Scheduled" tab
3. **Result:** ✅ This works!

### Test 2: Immediate Upload
1. Select video
2. Fill details
3. **DON'T** check "Schedule for later"
4. Click "🚀 Upload Now"
5. **Result:** Should upload immediately to social media

### Test 3: View Scheduled Uploads
1. Schedule multiple uploads at different times
2. Switch to "Scheduled" tab
3. Filter by "All", "Pending", etc.
4. **Result:** ✅ All UI features work!

### Test 4: Cancel Scheduled Upload
1. Go to "Scheduled" tab
2. Click 🗑️ (trash icon) on a pending upload
3. Confirm deletion
4. **Result:** ✅ Should disappear

---

## ❌ Step 7: What WON'T Work (Yet)

### Automatic Execution Won't Work
The **GitHub Actions worker cannot execute** scheduled uploads because:
1. Your uploads save to **Render's database**
2. Worker checks **GitHub's separate database** (artifacts)
3. These databases are not connected

### Testing GitHub Actions
If you try:
1. Go to: https://github.com/rosanmohan/one_click_upload/actions
2. Click "Scheduled Upload Worker"
3. Click "Run workflow"
4. **Result:** ❌ Will show "No pending uploads" even though you scheduled some

---

## 🔧 Solutions to Make It Fully Work

### Option A: API-Based Worker (Recommended)
**Make GitHub Actions call Render API**

The worker should:
1. Call Render backend API: `GET /api/scheduled/list?status=pending`
2. Get uploads ready to execute
3. Call Render API to execute each one
4. Update status via API

**Pros:** 
- ✅ Single source of truth (Render DB)
- ✅ Works with any backend deployment
- ✅ Easier to debug

**Cons:**
- Requires modifying worker script

### Option B: Shared Database
**Use PostgreSQL instead of SQLite**

Both Render and GitHub Actions connect to same PostgreSQL:
1. Create PostgreSQL on Render
2. Update backend to use PostgreSQL
3. GitHub Actions connects to same DB

**Pros:**
- ✅ True scheduled execution
- ✅ Scalable

**Cons:**
- Requires database migration
- More complex setup

### Option C: Backend-Based Scheduler
**Run scheduler on Render instead of GitHub Actions**

Add a cron job to Render backend:
1. Every 15 minutes, check for pending uploads
2. Execute them directly
3. No GitHub Actions needed

**Pros:**
- ✅ Simple architecture
- ✅ Everything in one place

**Cons:**
- Render free tier may not support background jobs

---

## 📝 Step 8: Document Current Status

### What Works ✅
- [x] Frontend deployment on GitHub Pages
- [x] Backend deployment on Render
- [x] API connection between frontend and backend
- [x] Scheduling uploads via UI
- [x] Viewing scheduled uploads
- [x] Canceling scheduled uploads
- [x] Immediate uploads (non-scheduled)
- [x] Database persistence on Render

### What Needs Fixing ❌
- [ ] Automatic execution of scheduled uploads
- [ ] GitHub Actions worker accessing correct database
- [ ] Worker logs showing scheduled uploads

---

## 🎯 Recommended Next Steps

### Short Term (Test What Works)
1. ✅ Test scheduling via deployed frontend
2. ✅ Test immediate uploads
3. ✅ Test UI features (view, cancel, filter)
4. ✅ Verify data persists across page reloads

### Medium Term (Make Worker Work)
Choose ONE solution:
- **Easiest:** Option A (API-based worker)
- **Most robust:** Option B (Shared database)
- **Simplest:** Option C (Backend scheduler)

### Long Term (Production Ready)
1. Implement chosen solution
2. Add monitoring and alerts
3. Add retry logic for failed uploads
4. Add user notifications

---

## 🔍 Debugging Production Issues

### Check Frontend Logs
1. Press F12
2. Console tab
3. Look for errors or API calls

### Check Backend Logs (Render)
1. Go to: https://dashboard.render.com/
2. Click your service
3. Click "Logs" tab
4. Watch for incoming requests

### Check GitHub Actions Logs
1. Go to: https://github.com/rosanmohan/one_click_upload/actions
2. Click workflow run
3. Expand steps to see detailed logs

### Check Database (Temporary)
Since Render uses SQLite, you can't easily access it remotely.
**Solution:** Add API endpoint to view database:

```
GET /api/scheduled/debug
```

Returns all uploads (for debugging only).

---

## ✅ Quick Production Test (Do This Now!)

### 5-Minute Test:
1. Open: https://rosanmohan.github.io/one_click_upload/
2. Click "Activate Server" → Should turn GREEN
3. Select a short test video (5-10 sec)
4. Fill: Title = "Prod Test", Description = "Testing"
5. ✅ Check "Schedule for later?"
6. Set time: 5 minutes from now
7. Click "📅 Schedule Upload"
8. **Expected:** Success + appears in "Scheduled" tab

### What This Tests:
- ✅ Frontend-backend connection
- ✅ File upload
- ✅ Schedule creation
- ✅ Database save
- ✅ UI display

### What This DOESN'T Test:
- ❌ Automatic execution (needs worker fix)

---

## 🚀 Ready to Test?

**Your deployed app:**
```
https://rosanmohan.github.io/one_click_upload/
```

**Start with the 5-minute test above!**

Then report back:
- Did server activation work?
- Did scheduling work?
- Did upload appear in "Scheduled" tab?

This will tell us if the **frontend + backend** are working correctly. The worker execution is a separate issue we'll fix next.

---

Good luck! 🎉
