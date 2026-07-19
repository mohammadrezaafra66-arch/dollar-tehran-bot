import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import cfg


class TorobDatabase:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or cfg.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seller_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_name TEXT,
                    phone TEXT,
                    email TEXT,
                    store_url TEXT,
                    torob_url TEXT,
                    price_on_torob INTEGER,
                    instagram TEXT,
                    telegram TEXT,
                    whatsapp TEXT,
                    crawl_status TEXT,
                    sync_status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_code TEXT,
                    product_name TEXT,
                    afrakala_price INTEGER,
                    lowest_rival INTEGER,
                    avg_rival REAL,
                    afrakala_rank INTEGER,
                    rival_count INTEGER,
                    diff_percent REAL,
                    ai_report TEXT,
                    sync_status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS torob_price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_url TEXT,
                    seller_url TEXT,
                    price_value INTEGER,
                    price_text TEXT,
                    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS torob_website_extractions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_id INTEGER,
                    external_url TEXT,
                    phone TEXT,
                    email TEXT,
                    instagram TEXT,
                    telegram TEXT,
                    whatsapp TEXT,
                    crawl_status TEXT,
                    crawled_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_leads(self, leads: list[dict[str, Any]]) -> int:
        if not leads:
            return 0
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO seller_leads (
                    store_name, phone, email, store_url, torob_url, price_on_torob,
                    instagram, telegram, whatsapp, crawl_status, sync_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        lead.get("store_name"),
                        lead.get("phone"),
                        lead.get("email"),
                        lead.get("store_url"),
                        lead.get("torob_url"),
                        lead.get("price_on_torob"),
                        lead.get("instagram"),
                        lead.get("telegram"),
                        lead.get("whatsapp"),
                        lead.get("crawl_status", "ok"),
                        lead.get("sync_status", "pending"),
                    )
                    for lead in leads
                ],
            )
            conn.commit()
        return len(leads)

    def get_pending_leads(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM seller_leads WHERE sync_status != 'synced' ORDER BY id DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_lead_synced(self, lead_ids: list[int]) -> int:
        if not lead_ids:
            return 0
        with self._connect() as conn:
            placeholders = ",".join("?" for _ in lead_ids)
            cursor = conn.execute(
                f"UPDATE seller_leads SET sync_status='synced' WHERE id IN ({placeholders})",
                lead_ids,
            )
            conn.commit()
        return cursor.rowcount

    def save_price_report(self, report: dict[str, Any]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO price_reports (
                    product_code, product_name, afrakala_price, lowest_rival, avg_rival,
                    afrakala_rank, rival_count, diff_percent, ai_report, sync_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.get("product_code"),
                    report.get("product_name"),
                    report.get("afrakala_price"),
                    report.get("lowest_rival"),
                    report.get("avg_rival"),
                    report.get("afrakala_rank"),
                    report.get("rival_count"),
                    report.get("diff_percent"),
                    report.get("ai_report"),
                    report.get("sync_status", "pending"),
                ),
            )
            conn.commit()
        return cursor.lastrowid

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            lead_total = conn.execute("SELECT COUNT(*) AS c FROM seller_leads").fetchone()["c"]
            pending = conn.execute("SELECT COUNT(*) AS c FROM seller_leads WHERE sync_status != 'synced'").fetchone()["c"]
            report_total = conn.execute("SELECT COUNT(*) AS c FROM price_reports").fetchone()["c"]
        return {"lead_total": lead_total, "pending_leads": pending, "price_report_total": report_total}
