# One Click Social Upload

A production-grade application to upload videos to Facebook, Instagram, and YouTube with a single click. Now supports multiple social media profiles!

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

## Configuration (Multi-Profile)

You can configure up to 3 different profiles (e.g., different YouTube channels or Facebook pages).
The system looks for environment variables prefixed with `PROFILE_{ID}_`.

### Default Profile (No prefix or Fallback)
Variables: `UPLOAD_FACEBOOK`, `FACEBOOK_PAGE_ID`, `YOUTUBE_TOKEN_FILE` etc.

### Profile 1 (e.g., Tech Channel)
Add these to your `backend/.env`:
```env
PROFILE_1_ALLOW_UPLOAD=true
PROFILE_1_UPLOAD_YOUTUBE=true
PROFILE_1_UPLOAD_FACEBOOK=false
PROFILE_1_YOUTUBE_TOKEN_FILE=youtube_token_1.json
PROFILE_1_FACEBOOK_PAGE_ID=123456789
```

### Profile 2 (e.g., Vlog Channel)
```env
PROFILE_2_ALLOW_UPLOAD=true
PROFILE_2_UPLOAD_YOUTUBE=true
PROFILE_2_YOUTUBE_TOKEN_FILE=youtube_token_2.json
```

**YouTube Tokens**:
- Ensure you have generated separate token files (e.g., `youtube_token_1.json`, `youtube_token_2.json`) by running the authentication flow for each channel.

## Usage

1. **Desktop**: Open `http://localhost:5173`.
2. **Select Profile**: Choose which profile you want to upload to from the dropdown.
3. **Select Video**: Choose your video file.
4. **Enter Details**: Title, Description, Hashtags.
5. **Upload**: Click "Upload to All Platforms".

**Note for Instagram**: 
Instagram upload via API requires the video URL to be **publicly accessible** on the internet.
- `http://192.168.1.3:8000/...` works for your phone to *control* the app, but Facebook servers *cannot* reach your local computer.
- To make Instagram upload work locally, you must use a tool like **ngrok** to expose port 8000.
