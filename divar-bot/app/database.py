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
