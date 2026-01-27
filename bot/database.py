import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "links.db"


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
            topic TEXT NOT NULL,
            shared_by TEXT,
            shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_id INTEGER,
            published INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_published ON links(published)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_shared_at ON links(shared_at)
    """)

    conn.commit()
    conn.close()


def add_link(url: str, topic: str, shared_by: str = None, title: str = None,
             description: str = None, message_id: int = None):
    """Add a new link to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for duplicates (same URL in last 7 days)
    cursor.execute("""
        SELECT id FROM links
        WHERE url = ? AND shared_at > datetime('now', '-7 days')
    """, (url,))

    if cursor.fetchone():
        conn.close()
        return False  # Duplicate

    cursor.execute("""
        INSERT INTO links (url, title, description, topic, shared_by, message_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (url, title, description, topic, shared_by, message_id))

    conn.commit()
    conn.close()
    return True


def get_unpublished_links(since_days: int = 7):
    """Get all unpublished links from the last N days."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM links
        WHERE published = 0
        AND shared_at > datetime('now', ? || ' days')
        ORDER BY topic, shared_at DESC
    """, (f"-{since_days}",))

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


# Initialize database on import
init_db()
