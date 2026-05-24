"""SQLite persistence for the Divar bot.

SQLite is the local durable source of truth for standalone deployments. The
schema is intentionally simple and migration-friendly so it can later move to
PostgreSQL without changing extraction logic.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


@dataclass(frozen=True)
class DivarStorageSettings:
    """Storage configuration."""

    db_path: Path = Path("database/divar_bot.sqlite")


class DivarStorage:
    """SQLite storage gateway for Divar runs, ads, leads, and failures."""

    def __init__(self, settings: Optional[DivarStorageSettings] = None) -> None:
        self.settings = settings or DivarStorageSettings()
        self.settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with production-safe pragmas."""

        conn = sqlite3.connect(self.settings.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema if missing."""

        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS divar_runs (
                    run_id TEXT PRIMARY KEY,
                    listing_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS divar_discovered_ads (
                    url TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    discovered_at TEXT NOT NULL,
                    processed_at TEXT,
                    error TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(run_id) REFERENCES divar_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS divar_raw_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    ad_url TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES divar_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS divar_final_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identity_key TEXT NOT NULL UNIQUE,
                    source_url TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    price_text TEXT NOT NULL DEFAULT '',
                    seller_name TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    city TEXT NOT NULL DEFAULT '',
                    district TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '',
                    lead_score INTEGER NOT NULL DEFAULT 1,
                    data_quality TEXT NOT NULL DEFAULT 'low',
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS divar_failed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    ad_url TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    error TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES divar_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS divar_pipeline_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES divar_runs(run_id)
                );
                """
            )

    def start_run(self, run_id: str, listing_url: str, metadata: Optional[Mapping[str, Any]] = None) -> None:
        """Create or update a pipeline run."""

        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO divar_runs(run_id, listing_url, status, created_at, updated_at, metadata_json)
                VALUES (?, ?, 'running', ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET status='running', updated_at=excluded.updated_at
                """,
                (run_id, listing_url, now, now, json.dumps(dict(metadata or {}), ensure_ascii=False)),
            )

    def finish_run(self, run_id: str, status: str = "completed") -> None:
        """Mark a run as finished."""

        with self.connect() as conn:
            conn.execute(
                "UPDATE divar_runs SET status=?, updated_at=? WHERE run_id=?",
                (status, datetime.utcnow().isoformat(), run_id),
            )

    def save_discovered_ads(self, run_id: str, ads: Iterable[Mapping[str, Any]]) -> None:
        """Persist discovered ad URLs."""

        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO divar_discovered_ads(url, run_id, slug, status, discovered_at)
                VALUES (?, ?, ?, 'pending', ?)
                """,
                [(str(ad.get("url", "")), run_id, str(ad.get("slug", "")), now) for ad in ads],
            )

    def pending_ads(self, run_id: str) -> list[Dict[str, Any]]:
        """Return pending ads for a run."""

        with self.connect() as conn:
            rows = conn.execute(
                "SELECT url, slug, status FROM divar_discovered_ads WHERE run_id=? AND status IN ('pending','failed') ORDER BY discovered_at ASC",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_ad_done(self, run_id: str, ad_url: str) -> None:
        """Mark an ad as processed."""

        with self.connect() as conn:
            conn.execute(
                "UPDATE divar_discovered_ads SET status='done', processed_at=?, error='' WHERE run_id=? AND url=?",
                (datetime.utcnow().isoformat(), run_id, ad_url),
            )

    def mark_ad_failed(self, run_id: str, ad_url: str, error: str) -> None:
        """Mark an ad as failed."""

        with self.connect() as conn:
            conn.execute(
                "UPDATE divar_discovered_ads SET status='failed', error=? WHERE run_id=? AND url=?",
                (error[:1000], run_id, ad_url),
            )

    def save_raw_detail(self, run_id: str, ad_url: str, payload: Mapping[str, Any]) -> None:
        """Persist raw detail payload."""

        with self.connect() as conn:
            conn.execute(
                "INSERT INTO divar_raw_details(run_id, ad_url, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (run_id, ad_url, json.dumps(dict(payload), ensure_ascii=False), datetime.utcnow().isoformat()),
            )

    def save_final_lead(self, identity_key: str, payload: Mapping[str, Any]) -> None:
        """Upsert final lead by identity key."""

        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO divar_final_leads(
                    identity_key, source_url, title, price_text, seller_name, phone, city, district,
                    description, lead_score, data_quality, payload_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(identity_key) DO UPDATE SET
                    title=excluded.title,
                    price_text=excluded.price_text,
                    seller_name=excluded.seller_name,
                    phone=excluded.phone,
                    city=excluded.city,
                    district=excluded.district,
                    description=excluded.description,
                    lead_score=excluded.lead_score,
                    data_quality=excluded.data_quality,
                    payload_json=excluded.payload_json,
                    updated_at=excluded.updated_at
                """,
                (
                    identity_key,
                    str(payload.get("source_url", "")),
                    str(payload.get("title", "")),
                    str(payload.get("price_text", "")),
                    str(payload.get("seller_name", "")),
                    str(payload.get("phone", "")),
                    str(payload.get("city", "")),
                    str(payload.get("district", "")),
                    str(payload.get("description", "")),
                    int(payload.get("lead_score", 1) or 1),
                    str(payload.get("data_quality", "low")),
                    json.dumps(dict(payload), ensure_ascii=False),
                    now,
                    now,
                ),
            )

    def record_failure(self, run_id: str, ad_url: str, stage: str, error: str) -> None:
        """Persist a failed item."""

        with self.connect() as conn:
            conn.execute(
                "INSERT INTO divar_failed_items(run_id, ad_url, stage, error, created_at) VALUES (?, ?, ?, ?, ?)",
                (run_id, ad_url, stage, error[:1000], datetime.utcnow().isoformat()),
            )

    def record_event(self, run_id: str, event_type: str, payload: Mapping[str, Any]) -> None:
        """Persist pipeline event."""

        with self.connect() as conn:
            conn.execute(
                "INSERT INTO divar_pipeline_events(run_id, event_type, payload_json, created_at) VALUES (?, ?, ?, ?)",
                (run_id, event_type, json.dumps(dict(payload), ensure_ascii=False), datetime.utcnow().isoformat()),
            )
