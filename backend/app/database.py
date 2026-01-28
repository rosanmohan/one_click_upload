# -*- coding: utf-8 -*-
import sys
import os

# Reconfigure stdout for UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
from datetime import datetime, timezone
from typing import List, Optional, Dict
import json
import os

DATABASE_PATH = os.path.join(os.getcwd(), "scheduled_uploads.db")

def safe_print(message: str):
    """Safely print messages with emojis, handling Windows encoding issues."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        ascii_message = message.encode('ascii', 'replace').decode('ascii')
        print(ascii_message)

def get_db_connection():
    """Create a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_uploads (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            hashtags TEXT,
            scheduled_time TEXT NOT NULL,
            video_filename TEXT NOT NULL,
            video_path TEXT NOT NULL,
            merge_videos INTEGER DEFAULT 0,
            upload_youtube INTEGER DEFAULT 0,
            upload_facebook INTEGER DEFAULT 0,
            upload_instagram INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            executed_at TEXT,
            error_message TEXT,
            facebook_post_id TEXT,
            instagram_media_id TEXT,
            youtube_video_id TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    safe_print(f"✅ Database initialized at: {DATABASE_PATH}")

def create_scheduled_upload(
    upload_id: str,
    profile_id: str,
    title: str,
    description: str,
    hashtags: str,
    scheduled_time: str,  # ISO 8601 format
    video_filename: str,
    video_path: str,
    merge_videos: bool = False,
    upload_youtube: bool = False,
    upload_facebook: bool = False,
    upload_instagram: bool = False
) -> Dict:
    """Create a new scheduled upload entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        INSERT INTO scheduled_uploads 
        (id, profile_id, title, description, hashtags, scheduled_time, 
         video_filename, video_path, merge_videos, upload_youtube, 
         upload_facebook, upload_instagram, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        upload_id, profile_id, title, description, hashtags, scheduled_time,
        video_filename, video_path, int(merge_videos), int(upload_youtube),
        int(upload_facebook), int(upload_instagram), 'pending', created_at
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "id": upload_id,
        "status": "pending",
        "scheduled_time": scheduled_time,
        "created_at": created_at
    }

def get_scheduled_uploads(profile_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """Retrieve scheduled uploads with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM scheduled_uploads WHERE 1=1"
    params = []
    
    if profile_id:
        query += " AND profile_id = ?"
        params.append(profile_id)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY scheduled_time ASC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_pending_uploads_to_execute() -> List[Dict]:
    """Get all pending uploads whose scheduled time has passed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_time = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        SELECT * FROM scheduled_uploads 
        WHERE status = 'pending' 
        AND scheduled_time <= ?
        ORDER BY scheduled_time ASC
    """, (current_time,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_upload_status(
    upload_id: str,
    status: str,
    error_message: Optional[str] = None,
    facebook_post_id: Optional[str] = None,
    instagram_media_id: Optional[str] = None,
    youtube_video_id: Optional[str] = None
):
    """Update the status of a scheduled upload."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    executed_at = datetime.now(timezone.utc).isoformat() if status in ['completed', 'failed'] else None
    
    cursor.execute("""
        UPDATE scheduled_uploads 
        SET status = ?, executed_at = ?, error_message = ?,
            facebook_post_id = ?, instagram_media_id = ?, youtube_video_id = ?
        WHERE id = ?
    """, (status, executed_at, error_message, facebook_post_id, instagram_media_id, youtube_video_id, upload_id))
    
    conn.commit()
    conn.close()

def delete_scheduled_upload(upload_id: str) -> bool:
    """Delete a scheduled upload and its associated video file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the video path before deleting
    cursor.execute("SELECT video_path, status FROM scheduled_uploads WHERE id = ?", (upload_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    video_path = row['video_path']
    status = row['status']
    
    # Only allow deletion if status is 'pending' or 'failed'
    if status not in ['pending', 'failed']:
        conn.close()
        return False
    
    # Delete from database
    cursor.execute("DELETE FROM scheduled_uploads WHERE id = ?", (upload_id,))
    conn.commit()
    conn.close()
    
    # Delete the video file(s) - handle both single path and JSON array of paths
    import json
    try:
        # Try to parse as JSON (multiple files)
        video_files = json.loads(video_path)
        # Multiple files - delete all
        for vf in video_files:
            if os.path.exists(vf):
                os.remove(vf)
        safe_print(f"🗑️ Deleted {len(video_files)} video files")
    except (json.JSONDecodeError, TypeError):
        # Single file path
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
                safe_print(f"🗑️ Deleted video file: {video_path}")
            except Exception as e:
                safe_print(f"⚠️ Could not delete video file {video_path}: {e}")
    
    return True

def get_upload_by_id(upload_id: str) -> Optional[Dict]:
    """Get a single scheduled upload by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scheduled_uploads WHERE id = ?", (upload_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

# Initialize database on module import
init_database()
