# -*- coding: utf-8 -*-
import sys
import os
import logging

# Reconfigure stdout for UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
from typing import List, Optional, Dict
import json
from urllib.parse import urlparse

# Get DB URL from env
DATABASE_URL = os.getenv('DATABASE_URL')
DATABASE_PATH = os.path.join(os.getcwd(), "scheduled_uploads.db")

logger = logging.getLogger(__name__)

def safe_print(message: str):
    """Safely print messages with emojis, handling Windows encoding issues."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        ascii_message = message.encode('ascii', 'replace').decode('ascii')
        print(ascii_message)

def get_db_connection():
    """Create a database connection (PostgreSQL or SQLite)."""
    if DATABASE_URL:
        # PostgreSQL Connection
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    else:
        # SQLite Connection
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_database():
    """Initialize the database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        # PostgreSQL Schema
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
        safe_print("✅ Database initialized (PostgreSQL)")
    else:
        # SQLite Schema
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
        safe_print(f"✅ Database initialized (SQLite) at: {DATABASE_PATH}")
    
    conn.commit()
    conn.close()

def dict_factory(cursor, row):
    """Convert DB row to dictionary, handling both SQLite and Postgres."""
    if DATABASE_URL:
        # Postgres passes realDictCursor (automatically dict-like)
        return dict(row)
    else:
        # SQLite
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

def execute_query(query: str, params: tuple = None, fetch_all: bool = False, fetch_one: bool = False, commit: bool = False):
    """Execute a query handling syntax differences."""
    conn = get_db_connection()
    
    if DATABASE_URL:
        # Use RealDictCursor for Postgres to get dictionary results
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Convert ? to %s for Postgres
        query = query.replace('?', '%s')
    else:
        cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if commit:
            conn.commit()
            
        if fetch_all:
            rows = cursor.fetchall()
            if not DATABASE_URL:
                # Manual dict conversion for SQLite
                return [dict(row) for row in rows]
            return [dict(r) for r in rows] # Postgres returns RealDictRow, convert to dict
            
        if fetch_one:
            row = cursor.fetchone()
            if not row:
                return None
            if not DATABASE_URL:
                return dict(row)
            return dict(row)
            
    finally:
        conn.close()

# --- Public API Functions (using helper) ---

def create_scheduled_upload(
    upload_id: str,
    profile_id: str,
    title: str,
    description: str,
    hashtags: str,
    scheduled_time: str,
    video_filename: str,
    video_path: str,
    merge_videos: bool = False,
    upload_youtube: bool = False,
    upload_facebook: bool = False,
    upload_instagram: bool = False
) -> Dict:
    """Create a new scheduled upload entry."""
    created_at = datetime.now(timezone.utc).isoformat()
    
    execute_query("""
        INSERT INTO scheduled_uploads 
        (id, profile_id, title, description, hashtags, scheduled_time, 
         video_filename, video_path, merge_videos, upload_youtube, 
         upload_facebook, upload_instagram, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        upload_id, profile_id, title, description, hashtags, scheduled_time,
        video_filename, video_path, int(merge_videos), int(upload_youtube),
        int(upload_facebook), int(upload_instagram), 'pending', created_at
    ), commit=True)
    
    return {
        "id": upload_id,
        "status": "pending",
        "scheduled_time": scheduled_time,
        "created_at": created_at
    }

def cleanup_old_uploads():
    """Delete completed uploads older than 24 hours."""
    # Calculate cutoff time (24 hours ago)
    from datetime import timedelta
    cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    
    # We first select the ones to delete to handle file cleanup if necessary, 
    # but for now we trust delete_scheduled_upload or just do a bulk db delete.
    # Bulk DB delete is safer for "log" cleanup, we assume files are already gone for completed uploads.
    # The prompt says "log info should be keep for 24 hour", implying database records.
    
    execute_query("""
        DELETE FROM scheduled_uploads 
        WHERE status = 'completed' 
        AND executed_at IS NOT NULL 
        AND executed_at < ?
    """, (cutoff_time,), commit=True)

def get_scheduled_uploads(profile_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """Retrieve scheduled uploads with optional filtering."""
    # Cleanup old completed uploads first
    try:
        cleanup_old_uploads()
    except Exception as e:
        logger.error(f"Failed to cleanup old uploads: {e}")

    query = "SELECT * FROM scheduled_uploads WHERE 1=1"
    params = []
    
    if profile_id:
        query += " AND profile_id = ?"
        params.append(profile_id)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY scheduled_time DESC"
    
    return execute_query(query, tuple(params), fetch_all=True)

def get_pending_uploads_to_execute() -> List[Dict]:
    """Get all pending uploads whose scheduled time has passed."""
    current_time = datetime.now(timezone.utc).isoformat()
    
    return execute_query("""
        SELECT * FROM scheduled_uploads 
        WHERE status = 'pending' 
        AND scheduled_time <= ?
        ORDER BY scheduled_time ASC
    """, (current_time,), fetch_all=True)

def update_upload_status(
    upload_id: str,
    status: str,
    error_message: Optional[str] = None,
    facebook_post_id: Optional[str] = None,
    instagram_media_id: Optional[str] = None,
    youtube_video_id: Optional[str] = None
):
    """Update the status of a scheduled upload."""
    executed_at = datetime.now(timezone.utc).isoformat() if status in ['completed', 'failed'] else None
    
    execute_query("""
        UPDATE scheduled_uploads 
        SET status = ?, executed_at = ?, error_message = ?,
            facebook_post_id = ?, instagram_media_id = ?, youtube_video_id = ?
        WHERE id = ?
    """, (status, executed_at, error_message, facebook_post_id, instagram_media_id, youtube_video_id, upload_id), commit=True)

def delete_scheduled_upload(upload_id: str) -> bool:
    """Delete a scheduled upload and its associated video file."""
    row = execute_query("SELECT video_path, status FROM scheduled_uploads WHERE id = ?", (upload_id,), fetch_one=True)
    
    if not row:
        return False
    
    video_path = row['video_path']
    status = row['status']
    
    # Only allow deletion if status is 'pending' or 'failed'
    if status not in ['pending', 'failed']:
        return False
    
    # Delete from database
    execute_query("DELETE FROM scheduled_uploads WHERE id = ?", (upload_id,), commit=True)
    
    # Delete the video file(s) logic (handling Cloudinary or local)
    # If video_path starts with http, it's a Cloudinary URL
    if video_path.startswith('http'):
         # It's a Cloudinary URL, we might want to delete it from Cloudinary
         # But we don't store the public_id in the DB simply yet, so we'll skip for now
         # or we can parse it.
         pass
    else:
        # Local file deletion logic
        import json
        try:
            video_files = json.loads(video_path)
            for vf in video_files:
                if os.path.exists(vf):
                    os.remove(vf)
            safe_print(f"🗑️ Deleted {len(video_files)} video files")
        except (json.JSONDecodeError, TypeError):
            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    safe_print(f"🗑️ Deleted video file: {video_path}")
                except Exception as e:
                    safe_print(f"⚠️ Could not delete video file {video_path}: {e}")
    
    return True

def get_upload_by_id(upload_id: str) -> Optional[Dict]:
    """Get a single scheduled upload by ID."""
    return execute_query("SELECT * FROM scheduled_uploads WHERE id = ?", (upload_id,), fetch_one=True)

# Initialize database on module import
init_database()
