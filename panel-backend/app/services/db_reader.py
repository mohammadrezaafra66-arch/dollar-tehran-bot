import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "panel-backend").exists():
        return cwd
    return Path(__file__).resolve().parents[3]


def _resolve_path(env_key: str, default_rel: str) -> Path:
    raw = os.getenv(env_key)
    if raw:
        candidate = Path(raw)
        if candidate.is_absolute():
            return candidate
        return _repo_root() / candidate
    return _repo_root() / default_rel


def _connect_sqlite(db_path: Path) -> Optional[sqlite3.Connection]:
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _boolish_to_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return 1
    if text in {"0", "false", "no", "n", "off", ""}:
        return 0
    return None


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def divar_stats() -> Dict[str, Any]:
    db_path = _resolve_path("DIVAR_DB_PATH", "divar-bot/data/divar_leads.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"total_leads": 0, "synced": 0, "messages_sent": 0, "pending": 0, "failed": 0}

    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM divar_leads").fetchone()["c"]
        synced = conn.execute("SELECT COUNT(*) AS c FROM divar_leads WHERE sync_status = 'synced'").fetchone()["c"]
        messages_sent = conn.execute("SELECT COUNT(*) AS c FROM divar_leads WHERE message_sent = 1").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) AS c FROM divar_leads WHERE sync_status = 'pending' OR extraction_status = 'pending'").fetchone()["c"]
        failed = conn.execute(
            "SELECT COUNT(*) AS c FROM divar_leads WHERE sync_status = 'failed' OR extraction_status = 'failed' OR message_status = 'failed'"
        ).fetchone()["c"]
    finally:
        conn.close()

    return {
        "total_leads": total,
        "synced": synced,
        "messages_sent": messages_sent,
        "pending": pending,
        "failed": failed,
    }


def divar_leads(limit: int = 100, offset: int = 0, status: Optional[str] = None, city: Optional[str] = None, message_sent: Optional[str] = None) -> Dict[str, Any]:
    db_path = _resolve_path("DIVAR_DB_PATH", "divar-bot/data/divar_leads.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"items": [], "total": 0}

    try:
        where_clauses: List[str] = []
        params: List[Any] = []

        if status:
            where_clauses.append("(extraction_status = ? OR sync_status = ?)")
            params.extend([status, status])
        if city:
            where_clauses.append("city = ?")
            params.append(city)
        if message_sent is not None:
            value = _boolish_to_int(message_sent)
            if value is not None:
                where_clauses.append("message_sent = ?")
                params.append(value)

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        query = f"SELECT * FROM divar_leads{where_sql} ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()
        total = conn.execute(f"SELECT COUNT(*) AS c FROM divar_leads{where_sql}", params[:-2]).fetchone()["c"]
    finally:
        conn.close()

    return {"items": [dict(row) for row in rows], "total": total}


def divar_send_log(limit: int = 50) -> Dict[str, Any]:
    db_path = _resolve_path("DIVAR_DB_PATH", "divar-bot/data/divar_leads.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"items": []}

    try:
        rows = conn.execute(
            "SELECT * FROM divar_send_log ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()

    return {"items": [dict(row) for row in rows]}


def divar_ai_stats() -> Dict[str, Any]:
    db_path = _resolve_path("DIVAR_DB_PATH", "divar-bot/data/divar_leads.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"total": 0, "analyzed": 0, "pending": 0, "failed": 0}

    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM divar_leads").fetchone()["c"]
        analyzed = conn.execute("SELECT COUNT(*) AS c FROM divar_leads WHERE ai_analyzed = 1").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) AS c FROM divar_leads WHERE ai_analyzed = 0").fetchone()["c"]
        failed = conn.execute("SELECT COUNT(*) AS c FROM divar_leads WHERE extraction_status = 'failed' OR sync_status = 'failed'").fetchone()["c"]
    finally:
        conn.close()

    return {"total": total, "analyzed": analyzed, "pending": pending, "failed": failed}


def torob_stats() -> Dict[str, Any]:
    db_path = _resolve_path("TOROB_DB_PATH", "torob-bot/data/torob.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"total_sellers": 0, "synced": 0, "total_reports": 0, "total_history": 0}

    try:
        total_sellers = conn.execute("SELECT COUNT(*) AS c FROM seller_leads").fetchone()["c"]
        synced = conn.execute("SELECT COUNT(*) AS c FROM seller_leads WHERE sync_status = 'synced'").fetchone()["c"]
        total_reports = conn.execute("SELECT COUNT(*) AS c FROM price_reports").fetchone()["c"]
        total_history = conn.execute("SELECT COUNT(*) AS c FROM torob_price_history").fetchone()["c"]
    finally:
        conn.close()

    return {"total_sellers": total_sellers, "synced": synced, "total_reports": total_reports, "total_history": total_history}


def torob_sellers(limit: int = 100, offset: int = 0, crawl_status: Optional[str] = None) -> Dict[str, Any]:
    db_path = _resolve_path("TOROB_DB_PATH", "torob-bot/data/torob.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"items": [], "total": 0}

    try:
        where_sql = ""
        params: List[Any] = []
        if crawl_status:
            where_sql = " WHERE crawl_status = ?"
            params.append(crawl_status)

        rows = conn.execute(
            f"SELECT * FROM seller_leads{where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        total = conn.execute(f"SELECT COUNT(*) AS c FROM seller_leads{where_sql}", params).fetchone()["c"]
    finally:
        conn.close()

    return {"items": [dict(row) for row in rows], "total": total}


def torob_seller_detail(seller_id: int) -> Optional[Dict[str, Any]]:
    db_path = _resolve_path("TOROB_DB_PATH", "torob-bot/data/torob.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return None

    try:
        row = conn.execute("SELECT * FROM seller_leads WHERE id = ?", (seller_id,)).fetchone()
    finally:
        conn.close()

    return dict(row) if row is not None else None


def torob_reports(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    db_path = _resolve_path("TOROB_DB_PATH", "torob-bot/data/torob.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"items": [], "total": 0}

    try:
        rows = conn.execute(
            "SELECT * FROM price_reports ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) AS c FROM price_reports").fetchone()["c"]
    finally:
        conn.close()

    return {"items": [dict(row) for row in rows], "total": total}


def google_maps_stats() -> Dict[str, Any]:
    db_path = _resolve_path("GOOGLE_MAPS_DB_PATH", "google-maps-bot/data/google_maps.db")
    conn = _connect_sqlite(db_path)
    if conn is None:
        return {"total_records": 0, "synced": 0, "pending": 0, "failed": 0}

    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM businesses").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) AS c FROM businesses WHERE status = 'pending'").fetchone()["c"]
        failed = conn.execute("SELECT COUNT(*) AS c FROM businesses WHERE status = 'failed'").fetchone()["c"]
        try:
            synced = conn.execute("SELECT COUNT(*) AS c FROM businesses WHERE sync_status = 'synced'").fetchone()["c"]
        except Exception:
            synced = 0
    finally:
        conn.close()

    return {"total_records": total, "synced": synced, "pending": pending, "failed": failed}
