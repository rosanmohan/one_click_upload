# One Click Social Upload

A production-grade application to upload videos to Facebook, Instagram, and YouTube with a single click.

## Structure

- **backend/**: FastAPI application handling video uploads and API integrations.
- **frontend/**: React + Vite application for the user interface.

## Prerequisites

- Python 3.8+
- Node.js & npm
- Facebook Page ID & Access Token
- Instagram Business Account ID
- YouTube `client_secret.json` and `youtube_token.json`

## Setup & Run

### 1. Backend

 Navigate to the backend directory:
 ```bash
 cd backend
 ```

 Activate the virtual environment:
 - Windows: `.\venv\Scripts\activate`
 - Mac/Linux: `source venv/bin/activate`

 (Dependencies are already installed, but if needed: `pip install -r requirements.txt`)

 Run the server:
 ```bash
 uvicorn app.main:app --reload
 ```
 The backend will run at `http://localhost:8000`.

### 2. Frontend

 Open a new terminal and navigate to the frontend directory:
 ```bash
 cd frontend
 ```

 Install dependencies (done, but if needed `npm install`):
 ```bash
 npm run dev
 ```
 The frontend will run at `http://localhost:5173`.

## Configuration

Update `backend/.env` with your actual API keys and tokens.
Ensure `client_secret.json` and `youtube_token.json` are present in the `backend/` directory for YouTube uploads.

### Environment Variables
```env
UPLOAD_FACEBOOK=true
FACEBOOK_PAGE_ID=...
FACEBOOK_ACCESS_TOKEN=...
UPLOAD_INSTAGRAM=true
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
UPLOAD_YOUTUBE=true
YOUTUBE_CLIENT_SECRET_FILE=client_secret.json
YOUTUBE_TOKEN_FILE=youtube_token.json
```

### 🔴 Fix YouTube Token Expiration (Important)
By default, Google tokens generated in "Testing" mode expire in **7 days**. To fix this:

1. Go to **Google Cloud Console** > **APIs & Services** > **OAuth consent screen**.
2. Under "Publishing status", click **PUBLISH APP** to promote it to "In production".
   - You **do not** need to submit for verification if you are the only user.
   - Just confirm the dialog.
3. Once in "Production", your refresh tokens will **never expire** (unless unused for 6 months).

### Regenerate YouTube Token
If your token has expired (error: `invalid_grant`), run the generator script:
```bash
cd backend
python generate_token.py
```
This will open a browser for you to login and create a new `youtube_token.json`.

## Usage

1. **Desktop**: Open `http://localhost:5173`.
2. **Select Video**: Choose your video file.
3. **Enter Details**: Title, Description, Hashtags.
4. **Upload**: Click "Upload to All Platforms".
5. **Progress**: Watch the progress bar as the video uploads.

**Note for Instagram**: 
Instagram upload via API requires the video URL to be **publicly accessible** on the internet.
- `http://192.168.1.3:8000/...` works for your phone to *control* the app, but Facebook servers *cannot* reach your local computer.
- To make Instagram upload work locally, you must use a tool like **ngrok** to expose port 8000.
