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

## Usage

1. **Desktop**: Open `http://localhost:5173`.
2. **Mobile**: Connect your phone to the same Wi-Fi as your computer. Open `http://192.168.1.3:5173`.
   - *Note: IP `192.168.1.3` is hardcoded. If your computer's IP changes, update `backend/.env` and `frontend/src/App.jsx`.*

### Steps
1. Select a video file.
2. Enter description and hashtags.
3. Click "Upload to All Platforms".
4. Status of each upload will be displayed.

**Note for Instagram**: 
Instagram upload via API requires the video URL to be **publicly accessible** on the internet.
- `http://192.168.1.3:8000/...` works for your phone to *control* the app, but Facebook servers *cannot* reach your local computer.
- To make Instagram upload work, you must use a tool like **ngrok** to expose port 8000 to the internet.
  - Run `ngrok http 8000`
  - Update `backend/.env` -> `BASE_URL=https://your-ngrok-url.ngrok-free.app`
  - Restart backend.

