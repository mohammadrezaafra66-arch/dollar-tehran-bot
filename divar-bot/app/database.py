CREATE_LEADS_TABLE = """
CREATE TABLE IF NOT EXISTS divar_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT UNIQUE NOT NULL,
    title TEXT,
    price_text TEXT,
    description TEXT,
    seller_name TEXT,
    phone TEXT,
    city TEXT,
    district TEXT,
    published_at TEXT,
    extraction_status TEXT DEFAULT 'pending',
    ai_analysis TEXT,
    ai_analyzed INTEGER DEFAULT 0,
    message_sent INTEGER DEFAULT 0,
    message_sent_at TEXT,
    message_status TEXT,
    profile_id TEXT DEFAULT 'divar-profile-1',
    sync_status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_SEND_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS divar_send_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    listing_url TEXT,
    phone TEXT,
    message_text TEXT,
    status TEXT,
    error_msg TEXT,
    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES divar_leads(id)
)
"""

CREATE_CHECKPOINT_TABLE = """
CREATE TABLE IF NOT EXISTS divar_checkpoints (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


import sqlite3
import os

DB_PATH = os.getenv("DIVAR_DB_PATH", "data/divar_leads.db")

def get_stats() -> dict:
    try:
        conn = sqlite3.connect(DB_PATH)
        total = conn.execute("SELECT COUNT(*) FROM divar_leads").fetchone()[0]
        synced = conn.execute(
            "SELECT COUNT(*) FROM divar_leads WHERE sync_status='synced'"
        ).fetchone()[0]
        messages = conn.execute(
            "SELECT COUNT(*) FROM divar_leads WHERE message_sent=1"
        ).fetchone()[0]
        conn.close()
        return {
            "total_leads": total,
            "synced": synced,
            "messages_sent": messages,
            "db_path": DB_PATH,
        }
    except Exception:
        return {"total_leads": 0, "synced": 0, "messages_sent": 0}
