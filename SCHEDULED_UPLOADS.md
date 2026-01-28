# Scheduled Video Upload Feature

## Overview

This feature allows you to schedule video uploads to social media platforms (YouTube, Facebook, Instagram) at a specific date and time. Videos are stored securely and automatically uploaded by a GitHub Actions worker that runs every 15 minutes.

## How It Works

### Architecture

```
┌─────────────────┐
│   Frontend UI   │
│  (React/Vite)   │
└────────┬────────┘
         │ Schedule Upload
         ▼
┌─────────────────┐
│  Backend API    │
│   (FastAPI)     │
└────────┬────────┘
         │ Stores in SQLite
         ▼
┌─────────────────┐
│  SQLite DB      │
│ + Video Files   │
└────────┬────────┘
         │ Reads every 15 min
         ▼
┌─────────────────┐
│ GitHub Actions  │
│ (scheduled_worker.py)
└────────┬────────┘
         │ Uploads when time matches
         ▼
┌─────────────────┐
│ Social Platforms│
│ YouTube/FB/IG   │
└─────────────────┘
```

## User Guide

### Scheduling an Upload

1. **Open the Application**
   - Navigate to `http://localhost:5173/one_click_upload/` (or your deployed URL)
   - Click "Activate Server" if needed

2. **Select Profile**
   - Choose the profile (e.g., "kids_fun" or "ayesha")

3. **Upload Video**
   - Drag & drop or select your video file
   - Enter title, description, and hashtags

4. **Schedule Upload**
   - Check "Schedule for later?"
   - Select date and time using the datetime picker
   - Click "📅 Schedule Upload"

5. **Confirmation**
   - You'll see a success message with the scheduled time
   - The app automatically switches to the "Scheduled" view

### Managing Scheduled Uploads

1. **View Scheduled Uploads**
   - Click the "Scheduled" tab in the header
   - Filter by status: All | Pending | Completed | Failed

2. **Cancel a Scheduled Upload**
   - Find the upload in the list
   - Click the trash icon (❌) on pending uploads
   - Confirm the cancellation

3. **Upload Status**
   - **Pending** 🕐 - Waiting to be uploaded
   - **Completed** ✅ - Successfully uploaded to all platforms
   - **Failed** ❌ - Upload encountered errors

## Developer Guide

### Backend Components

#### 1. Database (`app/database.py`)

SQLite database to store scheduled uploads:

```python
# Create a scheduled upload
from app.database import create_scheduled_upload

result = create_scheduled_upload(
    upload_id="unique-id",
    profile_id="kids_fun",
    title="My Video",
    description="Description here",
    hashtags="#fun #video",
    scheduled_time="2026-01-28T15:30:00",
    video_filename="video.mp4",
    video_path="/path/to/video.mp4",
    upload_youtube=True,
    upload_facebook=True,
    upload_instagram=True
)
```

#### 2. API Router (`app/routers/scheduled_uploads.py`)

REST API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scheduled/upload` | POST | Schedule a new upload |
| `/api/scheduled/list` | GET | List all scheduled uploads |
| `/api/scheduled/{upload_id}` | GET | Get specific upload details |
| `/api/scheduled/{upload_id}` | DELETE | Cancel a scheduled upload |

Example: Schedule upload via API

```bash
curl -X POST http://localhost:8000/api/scheduled/upload \
  -F "file=@video.mp4" \
  -F "title=My Video" \
  -F "description=Test" \
  -F "hashtags=#test" \
  -F "scheduled_time=2026-01-28T15:30:00" \
  -F "profile_id=kids_fun" \
  -F "upload_youtube=true" \
  -F "upload_facebook=true" \
  -F "upload_instagram=true"
```

#### 3. Worker Script (`scheduled_worker.py`)

Executed by GitHub Actions every 15 minutes:

```bash
# Run manually for testing
cd backend
python scheduled_worker.py
```

The worker:
1. Checks SQLite for pending uploads
2. Uploads videos to enabled platforms
3. Updates status (completed/failed)
4. Cleans up video files

### Frontend Components

#### 1. Main App (`src/App.jsx`)

- **State Management**
  - `isScheduled`: Toggle between immediate and scheduled upload
  - `scheduledDateTime`: Selected date/time
  - `currentView`: Switch between 'upload' and 'scheduled' views

- **Functions**
  - `handleScheduledUpload()`: Submit scheduled upload to API
  - `handleSubmit()`: Immediate upload (existing functionality)

#### 2. Scheduled Uploads View (`src/ScheduledUploads.jsx`)

Displays and manages scheduled uploads:
- Filter by status
- View upload details
- Cancel pending uploads
- Refresh list

### GitHub Actions Workflow

File: `.github/workflows/scheduled_worker.yml`

```yaml
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:  # Manual trigger
```

The workflow:
1. Checks out the repository
2. Sets up Python
3. Installs dependencies
4. Downloads the SQLite database (from artifacts)
5. Runs `scheduled_worker.py`
6. Uploads the updated database back to artifacts

### Required Secrets (GitHub)

Configure these in GitHub Settings → Secrets and variables → Actions:

#### Global Settings
- `ALLOW_UPLOAD` - Enable uploads (true/false)

#### Kids Fun Profile
- `UPLOAD_FACEBOOK`
- `UPLOAD_INSTAGRAM`
- `UPLOAD_YOUTUBE`
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`

#### Ayesha Profile
- `AYESHA_UPLOAD_FACEBOOK`
- `AYESHA_UPLOAD_INSTAGRAM`
- `AYESHA_UPLOAD_YOUTUBE`
- `AYESHA_FACEBOOK_PAGE_ID`
- `AYESHA_FACEBOOK_ACCESS_TOKEN`
- `AYESHA_INSTAGRAM_BUSINESS_ACCOUNT_ID`

#### Cloudinary
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

## Deployment

### Local Development

1. **Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate.ps1
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Test Scheduling**
   - Schedule a video for a few minutes in the future
   - Manually run the worker:
     ```bash
     cd backend
     python scheduled_worker.py
     ```

### Production (GitHub Actions)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add scheduled upload feature"
   git push origin main
   ```

2. **Configure Secrets**
   - Go to GitHub repository settings
   - Add all required secrets (see list above)

3. **Enable Workflow**
   - The workflow runs automatically every 15 minutes
   - Manual trigger: Actions → Scheduled Upload Worker → Run workflow

4. **Monitor**
   - Check Actions tab for workflow runs
   - View logs for upload status
   - Scheduled uploads appear in the frontend UI

## Database Schema

```sql
CREATE TABLE scheduled_uploads (
    id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    hashtags TEXT,
    scheduled_time TEXT NOT NULL,     -- ISO 8601 format
    video_filename TEXT NOT NULL,
    video_path TEXT NOT NULL,
    merge_videos INTEGER DEFAULT 0,
    upload_youtube INTEGER DEFAULT 0,
    upload_facebook INTEGER DEFAULT 0,
    upload_instagram INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',    -- pending, completed, failed
    created_at TEXT NOT NULL,
    executed_at TEXT,
    error_message TEXT,
    facebook_post_id TEXT,
    instagram_media_id TEXT,
    youtube_video_id TEXT
);
```

## Troubleshooting

### Upload Not Executing

1. **Check scheduled time**: Ensure it's in the future and in UTC
2. **Check GitHub Actions**: Look in Actions tab for failures
3. **Check secrets**: Verify all required secrets are set correctly
4. **Check logs**: Worker logs show detailed error messages

### Frontend Not Loading Scheduled Uploads

1. **Backend running?**: Ensure `http://localhost:8000` is accessible
2. **Network error**: Check browser console for API errors
3. **CORS**: Backend should allow frontend origin

### Worker Fails on GitHub Actions

1. **Check secrets**: Missing or incorrect secrets
2. **Check API tokens**: Facebook/Instagram tokens may have expired
3. **Check logs**: GitHub Actions logs show detailed errors

## API Reference

### POST /api/scheduled/upload

Schedule a new video upload.

**Request (multipart/form-data)**:
```
file: File
title: string
description: string
hashtags: string
scheduled_time: string (ISO 8601)
profile_id: string
upload_youtube: boolean
upload_facebook: boolean
upload_instagram: boolean
```

**Response**:
```json
{
  "success": true,
  "message": "Upload scheduled for 2026-01-28T15:30:00",
  "upload_id": "uuid",
  "data": { ... }
}
```

### GET /api/scheduled/list

List all scheduled uploads.

**Query Parameters**:
- `profile_id` (optional): Filter by profile
- `status` (optional): Filter by status (pending/completed/failed)

**Response**:
```json
{
  "success": true,
  "count": 2,
  "uploads": [
    {
      "id": "uuid",
      "profile_id": "kids_fun",
      "title": "My Video",
      "status": "pending",
      "scheduled_time": "2026-01-28T15:30:00",
      ...
    }
  ]
}
```

### DELETE /api/scheduled/{upload_id}

Cancel a scheduled upload.

**Response**:
```json
{
  "success": true,
  "message": "Scheduled upload cancelled successfully"
}
```

## Future Enhancements

- [ ] Email/SMS notifications when upload completes
- [ ] Recurring uploads (e.g., every Monday at 9 AM)
- [ ] Bulk scheduling from CSV
- [ ] Preview scheduled content before upload
- [ ] Analytics dashboard for scheduled uploads
- [ ] Platform-specific scheduling (different times for each platform)
