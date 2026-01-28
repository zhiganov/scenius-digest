import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Use /app/data for Fly.io volume, otherwise local directory
DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).parent))
DB_PATH = DATA_DIR / "links.db"


def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            title TEXT,
            description TEXT,
            group_id TEXT,
            group_name TEXT,
            topic TEXT NOT NULL,
            shared_by TEXT,
            shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_id INTEGER,
            message_text TEXT,
            published INTEGER DEFAULT 0
        )
    """)

    # Migration: add columns if they don't exist (for existing DBs)
    cursor.execute("PRAGMA table_info(links)")
    columns = [col[1] for col in cursor.fetchall()]

    if "message_text" not in columns:
        cursor.execute("ALTER TABLE links ADD COLUMN message_text TEXT")

    if "group_id" not in columns:
        cursor.execute("ALTER TABLE links ADD COLUMN group_id TEXT")

    if "group_name" not in columns:
        cursor.execute("ALTER TABLE links ADD COLUMN group_name TEXT")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_published ON links(published)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_shared_at ON links(shared_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_group_published ON links(group_id, published)
    """)

    conn.commit()
    conn.close()


def add_link(url: str, topic: str, shared_by: str = None, title: str = None,
             description: str = None, message_id: int = None, message_text: str = None,
             group_id: str = None, group_name: str = None):
    """Add a new link to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for duplicates (same URL in same group in last 7 days)
    if group_id:
        cursor.execute("""
            SELECT id FROM links
            WHERE url = ? AND group_id = ? AND shared_at > datetime('now', '-7 days')
        """, (url, group_id))
    else:
        # Legacy: check globally if no group_id
        cursor.execute("""
            SELECT id FROM links
            WHERE url = ? AND shared_at > datetime('now', '-7 days')
        """, (url,))

    if cursor.fetchone():
        conn.close()
        return False  # Duplicate

    cursor.execute("""
        INSERT INTO links (url, title, description, group_id, group_name, topic, shared_by, message_id, message_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (url, title, description, group_id, group_name, topic, shared_by, message_id, message_text))

    conn.commit()
    conn.close()
    return True


def get_unpublished_links(since_days: int = 7, group_id: str = None):
    """Get all unpublished links from the last N days, optionally filtered by group."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if group_id:
        cursor.execute("""
            SELECT * FROM links
            WHERE published = 0
            AND group_id = ?
            AND shared_at > datetime('now', ? || ' days')
            ORDER BY topic, shared_at DESC
        """, (group_id, f"-{since_days}"))
    else:
        cursor.execute("""
            SELECT * FROM links
            WHERE published = 0
            AND shared_at > datetime('now', ? || ' days')
            ORDER BY group_name, topic, shared_at DESC
        """, (f"-{since_days}",))

    links = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return links


def get_links_by_group(group_id: str, since_days: int = 7, published: bool = None):
    """Get links for a specific group."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT * FROM links
        WHERE group_id = ?
        AND shared_at > datetime('now', ? || ' days')
    """
    params = [group_id, f"-{since_days}"]

    if published is not None:
        query += " AND published = ?"
        params.append(1 if published else 0)

    query += " ORDER BY topic, shared_at DESC"

    cursor.execute(query, params)
    links = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return links


def mark_as_published(link_ids: list):
    """Mark links as published."""
    if not link_ids:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(link_ids))
    cursor.execute(f"""
        UPDATE links SET published = 1 WHERE id IN ({placeholders})
    """, link_ids)

    conn.commit()
    conn.close()


def get_stats(group_id: str = None):
    """Get link statistics, optionally for a specific group."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if group_id:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN published = 0 THEN 1 ELSE 0 END) as unpublished,
                   SUM(CASE WHEN published = 1 THEN 1 ELSE 0 END) as published
            FROM links WHERE group_id = ?
        """, (group_id,))
    else:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN published = 0 THEN 1 ELSE 0 END) as unpublished,
                   SUM(CASE WHEN published = 1 THEN 1 ELSE 0 END) as published
            FROM links
        """)

    row = cursor.fetchone()
    conn.close()
    return {"total": row[0] or 0, "unpublished": row[1] or 0, "published": row[2] or 0}


# Initialize database on import
init_db()
