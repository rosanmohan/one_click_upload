# ✅ Production Testing Checklist

## 🎯 Your URLs
- Frontend: `https://rosanmohan.github.io/one_click_upload/`
- Backend: `https://your-render-service.onrender.com`
- GitHub Actions: `https://github.com/rosanmohan/one_click_upload/actions`

---

## 📋 Pre-Test Checklist

### GitHub Secrets (Required)
Go to: Settings → Secrets and variables → Actions

- [ ] `VITE_API_URL` = Your Render backend URL
- [ ] `ALLOW_UPLOAD` = `true`
- [ ] `UPLOAD_FACEBOOK` = `true`
- [ ] `FACEBOOK_PAGE_ID` = Your ID
- [ ] `FACEBOOK_ACCESS_TOKEN` = Your token
- [ ] `INSTAGRAM_BUSINESS_ACCOUNT_ID` = Your ID
- [ ] `CLOUDINARY_CLOUD_NAME` = Your name
- [ ] `CLOUDINARY_API_KEY` = Your key
- [ ] `CLOUDINARY_API_SECRET` = Your secret

---

## 🧪 Test Sequence

### Test 1: Server Connection
- [ ] Open deployed frontend
- [ ] Click "Activate Server"
- [ ] ✅ Should turn GREEN within 5-10 seconds

**If RED:** Backend is down or VITE_API_URL is wrong

---

### Test 2: Schedule Upload
- [ ] Select short video (5-10 sec)
- [ ] Title: "Test Scheduled Upload"
- [ ] Description: "Testing production"
- [ ] Hashtags: "#test"
- [ ] ✅ Check "Schedule for later?"
- [ ] Set time: 10 minutes from now
- [ ] Click "📅 Schedule Upload"
- [ ] ✅ Success message appears
- [ ] ✅ Switches to "Scheduled" tab
- [ ] ✅ Upload appears with "Pending" status

**If fails:** Check browser console (F12) for errors

---

### Test 3: Verify Persistence
- [ ] Hard refresh page (Ctrl+Shift+R)
- [ ] Click "Activate Server" again
- [ ] Go to "Scheduled" tab
- [ ] ✅ Upload still there

**If disappeared:** Database didn't save - backend issue

---

### Test 4: Immediate Upload (Bonus)
- [ ] Select video
- [ ] Fill details
- [ ] DON'T check "Schedule for later?"
- [ ] Click "🚀 Upload Now"
- [ ] Wait for completion
- [ ] ✅ Success message
- [ ] ✅ Video appears on social media

**This tests** that uploads actually work

---

### Test 5: Cancel Scheduled
- [ ] Go to "Scheduled" tab
- [ ] Click 🗑️ on a pending upload
- [ ] Confirm deletion
- [ ] ✅ Upload disappears

---

## ⚠️ Known Limitations

### ❌ What Won't Work Yet:
- **Automatic execution at scheduled time**
  - Reason: GitHub Actions uses separate database
  - Worker won't find your uploads
  - Needs architecture fix

### ✅ What Will Work:
- Scheduling via UI
- Viewing scheduled uploads 
- Canceling scheduled uploads
- Immediate (non-scheduled) uploads
- All UI features

---

## 🔍 Troubleshooting

### Server Won't Activate (Stays Red)
**Check:**
1. Is Render backend running?
   - Go to Render dashboard
   - Check service status
2. Is backend URL correct in GitHub secrets?
   - Check `VITE_API_URL` value
3. Open backend health endpoint:
   - `your-backend-url.onrender.com/health`
   - Should show `{"status":"ok"}`

### Upload Doesn't Save
**Check:**
1. Browser console (F12)
   - Look for POST request errors
2. Backend logs in Render
   - Go to Render → Service → Logs
   - Look for incoming requests
3. File size
   - Very large files may timeout
   - Use small test videos

### Can't Find Deployed URLs
**Frontend:**
- GitHub → Settings → Pages
- Look for "Your site is live at..."

**Backend:**
- Render Dashboard
- Your service → URL at top

---

## 📊 Success Criteria

### Minimum (Frontend + Backend)
- [x] Frontend loads
- [x] Server activates (green)
- [x] Can schedule upload
- [x] Upload appears in "Scheduled" tab
- [x] Upload persists after refresh

### Desired (Full Feature)
- [x] All of above +
- [ ] GitHub Actions executes uploads ← Needs fix
- [ ] Status changes to "Completed"
- [ ] Video posts at scheduled time

---

## 🚀 Quick Start Commands

### Find Backend URL:
```bash
# Check your Render dashboard at:
https://dashboard.render.com/
```

### Test Backend Health:
```bash
curl https://your-backend-url.onrender.com/health
# Should return: {"status":"ok"}
```

### View GitHub Actions:
```bash
# Open in browser:
https://github.com/rosanmohan/one_click_upload/actions
```

---

## 📝 Report Template

After testing, document results:

```markdown
## Test Results - [Date]

### Environment:
- Frontend: [URL]
- Backend: [URL]

### Test 1 - Server Connection:
- Result: [PASS/FAIL]
- Notes: [any issues]

### Test 2 - Schedule Upload:
- Result: [PASS/FAIL]
- Upload ID: [if successful]
- Notes: [any issues]

### Test 3 - Persistence:
- Result: [PASS/FAIL]
- Notes: [any issues]

### Errors Encountered:
[paste any error messages from console]

### Screenshots:
[attach if helpful]
```

---

## ⏭️ Next Steps

After confirming frontend + backend work:

### Option A: Fix GitHub Actions Worker
Modify worker to call Render API instead of using local DB

### Option B: Use Shared Database  
Migrate from SQLite to PostgreSQL that both can access

### Option C: Backend Scheduler
Run scheduler on Render instead of GitHub Actions

---

## 🆘 Need Help?

1. **Check logs:**
   - Browser: F12 → Console
   - Backend: Render → Logs
   - Worker: GitHub → Actions → Run logs

2. **Common issues:**
   - CORS errors: Backend CORS not configured
   - 404 errors: Wrong API URL
   - 500 errors: Backend crashed (check Render logs)
   - Timeout: Render backend sleeping (first request slow)

3. **Render Free Tier Note:**
   - Backend "spins down" after 15 min inactivity
   - First request takes 30-60 seconds to wake up
   - Be patient on first "Activate Server" click

---

✅ **Start here:** https://rosanmohan.github.io/one_click_upload/

Good luck! 🎉
