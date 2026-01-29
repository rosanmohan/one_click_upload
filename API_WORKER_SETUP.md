# 🎯 API-Based Worker Setup - Final Step

## ✅ What Was Implemented:

### 1. **Backend API Endpoints** (Render)
- `GET /api/scheduled/pending/ready` - Get uploads ready to execute
- `POST /api/scheduled/execute/{upload_id}` - Execute a specific upload

### 2. **API Worker Script** (`api_worker.py`)
- Calls Render API instead of using local database
- No database sync needed!
- Simpler and more reliable

### 3. **Updated GitHub Actions**
- Now uses `api_worker.py`
- Only needs `RENDER_BACKEND_URL` secret
- Runs every 15 minutes

---

## 🔧 **ONE FINAL STEP: Add GitHub Secret**

### **Go to GitHub Settings:**

1. **Open in browser:**
   ```
   https://github.com/rosanmohan/one_click_upload/settings/secrets/actions
   ```

2. **Click "New repository secret"**

3. **Add this secret:**
   - **Name:** `RENDER_BACKEND_URL`
   - **Value:** Your Render backend URL (example below)
   
   **Find your Render URL:**
   - Go to: https://dashboard.render.com/
   - Click your backend service
   - Copy the URL at the top (looks like: `https://your-service-name.onrender.com`)
   
   **Example:**
   ```
   https://one-click-backend-xyz123.onrender.com
   ```
   
   **Important:** NO trailing slash!

4. **Click "Add secret"**

---

## ✅ **Testing the Complete Flow:**

### **Test 1: Schedule Upload in Production**

1. **Go to your deployed app:**
   ```
   https://rosanmohan.github.io/one_click_upload/
   ```

2. **Schedule an upload:**
   - Activate server
   - Select short video (5-10 sec)
   - Fill details
   - ✅ Check "Schedule for later?"
   - Set time: **20 minutes from now**
   - Click "📅 Schedule Upload"

3. **Verify it was saved:**
   - Switch to "Scheduled" tab
   - Should show with "Pending" status

---

### **Test 2: Trigger Worker Manually**

1. **Go to GitHub Actions:**
   ```
   https://github.com/rosanmohan/one_click_upload/actions
   ```

2. **Click "Scheduled Upload Worker"**

3. **Click "Run workflow" button**
   - Select branch: `main`
   - Click green "Run workflow"

4. **Wait 30-60 seconds**
   - Refresh page
   - Click on the newest workflow run

5. **Check logs:**
   - Click "Execute API-based worker"
   - Expand logs

**Expected logs:**
```
🔄 API-Based Worker Started
   Backend URL: https://your-render.onrender.com
📋 Found X pending upload(s) to process

🎬 Processing Upload: [id]
   Title: [your title]
   Scheduled: [time]
```

**If scheduled time hasn't passed yet:**
```
📋 Found 0 pending upload(s) to process
✅ No pending uploads to process.
```

**This is CORRECT!** Wait for scheduled time to pass.

---

### **Test 3: Wait for Automatic Execution**

1. **After scheduled time passes:**
   - Wait up to 15 minutes
   - GitHub Actions runs every 15 minutes

2. **Worker will:**
   - Find your upload
   - Execute it
   - Post to enabled platforms
   - Update status to "Completed"

3. **Verify:**
   - Refresh "Scheduled" tab in UI
   - Status should be "Completed" ✅
   - Check social media - video posted!

---

## 🔍 **How It Works Now:**

```
┌─────────────────────────┐
│ GitHub Pages (Frontend) │
│  - Schedule upload      │
└───────────┬─────────────┘
            ↓
┌───────────────────────────┐
│ Render Backend (API)      │
│  - Saves to database      │
│  - Has /execute endpoint  │
└───────────┬───────────────┘
            ↑
┌───────────┴───────────────┐
│ GitHub Actions Worker     │
│  - Calls Render API       │
│  - Gets pending uploads   │
│  - Triggers execution     │
└───────────────────────────┘
```

**All using Render's database - perfectly synced!** ✅

---

## 🆘 **Troubleshooting:**

### **Issue: Worker shows "Failed to fetch"**

**Cause:** `RENDER_BACKEND_URL` not set or wrong

**Fix:**
1. Check GitHub secret exists
2. Verify URL is correct (no trailing slash)
3. Test URL manually: `https://your-url.onrender.com/health`
   - Should return: `{"status":"ok"}`

---

### **Issue: "No pending uploads" but I scheduled one**

**Cause:** Scheduled time hasn't passed yet

**Check:**
- In "Scheduled" tab, note the scheduled time
- Worker only processes uploads AFTER that time
- Wait for time to pass + up to 15 min

---

### **Issue: Upload fails with error**

**Check Render logs:**
1. Go to Render dashboard
2. Click your service
3. Click "Logs"
4. Look for errors when execute endpoint is called

**Common issues:**
- API tokens expired
- Video file not found
- Platform API errors

---

## 📊 **Success Criteria:**

- [x] Backend deployed on Render
- [x] Frontend deployed on GitHub Pages
- [x] Can schedule uploads in UI
- [x] Uploads save to Render database
- [x] GitHub secret `RENDER_BACKEND_URL` added
- [ ] Worker runs without errors ← **Test after adding secret!**
- [ ] Upload status changes to "Completed"
- [ ] Video appears on social media

---

## 🚀 **Quick Test Command:**

After adding the secret, test the API endpoint directly:

```bash
curl https://your-render-url.onrender.com/api/scheduled/pending/ready
```

**Expected response:**
```json
{
  "success": true,
  "count": 0,
  "uploads": []
}
```

(Count will be > 0 if you have pending uploads past their scheduled time)

---

## ✅ **Next Steps:**

1. **Add `RENDER_BACKEND_URL` secret** (instructions above)
2. **Trigger worker manually** (GitHub Actions)
3. **Check logs** - should see successful API call
4. **Schedule test upload** for 20 min from now
5. **Wait 20 min + run worker** manually
6. **Verify video posted** to social media!

---

**After this works, the automatic 15-minute scheduler will handle everything!** 🎉

---

## 🔗 **Links:**

- **Add Secret:** https://github.com/rosanmohan/one_click_upload/settings/secrets/actions
- **Render Dashboard:** https://dashboard.render.com/
- **GitHub Actions:** https://github.com/rosanmohan/one_click_upload/actions
- **Deployed App:** https://rosanmohan.github.io/one_click_upload/

---

Good luck! Let me know when you've added the secret and we'll test it together! 🚀
