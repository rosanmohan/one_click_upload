# Deployment Guide

This application consists of two parts: Frontend (React) and Backend (FastAPI). 
Since GitHub Actions runners are temporary, you cannot "host" the backend on them. You must deploy the backend to a cloud provider.

## Part 1: Backend Deployment (Render.com)
We will use **Render** (free tier available) to host the Python backend.

1.  **Push your code to GitHub**.
2.  **Sign up/Log in to [Render.com](https://render.com)** using your GitHub account.
3.  Click **New +** -> **Web Service**.
4.  Connect your GitHub repository (`one_click_upload`).
5.  **Configure the Service**:
    *   **Name**: `one-click-backend` (or similar)
    *   **Root Directory**: `backend`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6.  **Environment Variables**:
    *   Scroll down to "Environment Variables" and Add the following from your local `.env`:
        *   `ALLOW_UPLOAD` = `true`
        *   `UPLOAD_FACEBOOK`, `UPLOAD_INSTAGRAM`... (set your preferences)
        *   `FACEBOOK_PAGE_ID`, `FACEBOOK_ACCESS_TOKEN`, etc.
        *   `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
        *   `BASE_URL`: **IMPORTANT**. Set this to your Render URL once created (e.g., `https://one-click-backend.onrender.com`).
    *   **Files**:
        *   For `client_secret.json` and `youtube_token.json`, Render has a "Secret Files" option (paid) or you can base64 encode them into specific env vars and decode in code. 
        *   *Simpler Option for YouTube*: If you can't use Secret Files, you might need to commit `client_secret.json` (risky) or disable YouTube upload on production for now.
7.  Click **Create Web Service**.
8.  **Wait for deployment**. Once valid, copy the URL (e.g., `https://one-click-backend.onrender.com`).

## Part 2: Frontend Deployment (GitHub Pages)

1.  **Go to your GitHub Repository Settings**.
2.  **Secrets and variables** -> **Actions**.
3.  Click **New repository secret**.
4.  **Name**: `VITE_API_URL`
5.  **Value**: The Render Backend URL you just copied (e.g., `https://one-click-backend.onrender.com`). **Do not add a trailing slash**.
6.  **Go to "Pages"** in Settings.
    *   Under "Build and deployment", select **GitHub Actions**.
7.  **Push your changes** to the `main` branch.
    *   The `.github/workflows/deploy-frontend.yml` workflow will automatically run.
    *   It will build your React app and deploy it to GitHub Pages.
8.  Once finished, your app will be live at `https://<your-username>.github.io/one_click_upload/`.

## Summary
- **Frontend**: Hosted on GitHub Pages (Free).
- **Backend**: Hosted on Render (Free).
- **Communication**: Frontend sends video to Backend URL -> Backend uploads to Socials.
