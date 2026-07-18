import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DIVAR_DB_PATH", "data/divar_leads.db")


def log_sent(lead_id: int, listing_url: str, phone: str,
             message_text: str, status: str, error_msg: str = "") -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            INSERT INTO divar_send_log
            (lead_id, listing_url, phone, message_text, status, error_msg, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lead_id, listing_url, phone, message_text, status, error_msg,
              datetime.now().isoformat()))
        conn.execute("""
            UPDATE divar_leads
            SET message_sent = ?,
                message_sent_at = ?,
                message_status = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            1 if status == "sent" else 0,
            datetime.now().isoformat(),
            status,
            datetime.now().isoformat(),
            lead_id,
        ))
        conn.commit()
    finally:
        conn.close()


def get_daily_sent_count() -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        today = datetime.now().date().isoformat()
        row = conn.execute(
            "SELECT COUNT(*) FROM divar_send_log WHERE status='sent' AND sent_at LIKE ?",
            (f"{today}%",)
        ).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()
