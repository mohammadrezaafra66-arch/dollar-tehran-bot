from __future__ import annotations

import json
import os
import re
import sqlite3
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
TEHRAN = timezone(timedelta(hours=3, minutes=30))
UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def gregorian_to_jalali(gy: int, gm: int, gd: int):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    jm = 1 + days // 31 if days < 186 else 7 + (days - 186) // 30
    jd = 1 + (days % 31 if days < 186 else (days - 186) % 30)
    return jy, jm, jd


def fa_num(value: Any) -> str:
    return str(value).translate(EN_TO_FA)


def jalali_stamp(dt: datetime | None = None) -> dict[str, str]:
    dt = dt or now_tehran()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TEHRAN)
    tehran_dt = dt.astimezone(TEHRAN)
    jy, jm, jd = gregorian_to_jalali(tehran_dt.year, tehran_dt.month, tehran_dt.day)
    return {
        "gregorian": tehran_dt.isoformat(),
        "utc": tehran_dt.astimezone(UTC).isoformat(),
        "jalali_date": f"{jy:04d}/{jm:02d}/{jd:02d}",
        "jalali_date_fa": f"{fa_num(jy)}/{fa_num(str(jm).zfill(2))}/{fa_num(str(jd).zfill(2))}",
        "iran_time": tehran_dt.strftime("%H:%M:%S"),
        "iran_time_fa": fa_num(tehran_dt.strftime("%H:%M:%S")),
    }


def clean_number(text: str) -> int:
    if text is None:
        raise ValueError("empty number")
    s = str(text).translate(FA_DIGITS)
    s = s.replace(",", "").replace("،", "").replace(" ", "").replace("\u200c", "")
    m = re.search(r"-?\d+", s)
    if not m:
        raise ValueError(f"number not found in {text!r}")
    return int(m.group(0))


def normalize(value: int, unit: str) -> int:
    unit = (unit or "toman").lower()
    if unit in ("rial", "irr", "ریال"):
        return round(value / 10)
    return int(value)


@dataclass
class SourceResult:
    indicator_code: str
    indicator_name: str
    source_code: str
    source_name: str
    source_url: str
    channel: str
    price_kind: str
    input_unit: str
    output_unit: str
    ok: bool
    value_toman: int | None
    raw_value: str | None
    quality_score: float
    latency_ms: int
    error: str | None
    observed_at_utc: str
    observed_at_tehran: str
    observed_at_jalali: str
    observed_time_iran: str


def load_config(path: str = "configs/indicators.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_html(url: str, timeout: int, user_agent: str) -> str:
    r = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": user_agent,
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.7",
            "Cache-Control": "no-cache",
        },
    )
    r.raise_for_status()
    return r.text


def extract_by_step(html_text: str, step: dict) -> str:
    kind = step.get("kind")
    soup = BeautifulSoup(html_text, "html.parser")
    if kind == "css":
        el = soup.select_one(step["selector"])
        if not el:
            raise ValueError("css selector not found")
        return el.get_text(" ", strip=True)
    if kind == "regex":
        m = re.search(step["pattern"], html_text, re.S)
        if not m:
            raise ValueError("regex not matched")
        return m.group(1) if m.groups() else m.group(0)
    if kind == "row_contains":
        words = step.get("contains", [])
        number_pattern = step.get("number_pattern", r"([0-9۰-۹٠-٩]{1,3}(?:[,،][0-9۰-۹٠-٩]{3})+)")
        index = int(step.get("index", 0))
        for row in soup.find_all(["tr", "div", "article", "section"]):
            txt = row.get_text(" ", strip=True)
            if all(w in txt for w in words):
                nums = re.findall(number_pattern, txt)
                if nums and len(nums) > index:
                    return nums[index]
        raise ValueError("row with requested words not found")
    raise ValueError(f"unknown extractor kind: {kind}")


def _stamp_pair() -> tuple[datetime, dict[str, str]]:
    dt = now_tehran()
    return dt, jalali_stamp(dt)


def extract_source(indicator: dict, source: dict, app: dict) -> SourceResult:
    started = time.perf_counter()
    dt, stamp = _stamp_pair()
    base = {
        "indicator_code": indicator["code"],
        "indicator_name": indicator["name"],
        "source_code": source["code"],
        "source_name": source["name"],
        "source_url": source["url"],
        "channel": source.get("channel", "website"),
        "price_kind": source.get("price_kind", "current"),
        "input_unit": source.get("unit", "toman"),
        "output_unit": "toman",
        "observed_at_utc": stamp["utc"],
        "observed_at_tehran": stamp["gregorian"],
        "observed_at_jalali": stamp["jalali_date"],
        "observed_time_iran": stamp["iran_time"],
    }
    try:
        if source["url"].startswith("manual://"):
            raw = str(source["manual_value"])
        else:
            page = fetch_html(source["url"], app.get("timeout_seconds", 20), app.get("user_agent", "Mozilla/5.0"))
            raw = None
            last_error = None
            for step in source.get("extractors", []):
                try:
                    raw = extract_by_step(page, step)
                    break
                except Exception as exc:
                    last_error = str(exc)
            if raw is None:
                raise ValueError(last_error or "no extractor matched")
        value = normalize(clean_number(raw), source.get("unit", "toman"))
        latency_ms = int((time.perf_counter() - started) * 1000)
        return SourceResult(**base, ok=True, value_toman=value, raw_value=raw, quality_score=1.0, latency_ms=latency_ms, error=None)
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return SourceResult(**base, ok=False, value_toman=None, raw_value=None, quality_score=0.0, latency_ms=latency_ms, error=f"{type(exc).__name__}: {exc}")


def ensure_db(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30)
    con.execute("pragma journal_mode=WAL")
    con.execute("pragma synchronous=NORMAL")
    con.execute(
        """
        create table if not exists indicators(
            code text primary key,
            name text not null,
            unit text not null default 'toman',
            category text,
            config_json text,
            updated_at text not null
        )
        """
    )
    con.execute(
        """
        create table if not exists sources(
            code text primary key,
            indicator_code text not null,
            name text not null,
            url text not null,
            channel text not null default 'website',
            price_kind text not null,
            input_unit text not null,
            enabled integer not null,
            priority integer not null default 100,
            weight real not null default 1,
            poll_interval_seconds integer not null default 60,
            config_json text,
            updated_at text not null
        )
        """
    )
    con.execute(
        """
        create table if not exists observations(
            id integer primary key autoincrement,
            indicator_code text not null,
            source_code text not null,
            price_kind text not null,
            value_toman integer,
            raw_value text,
            ok integer not null,
            quality_score real not null,
            latency_ms integer,
            error text,
            observed_at_utc text not null,
            observed_at_tehran text not null,
            observed_at_jalali text not null,
            observed_time_iran text not null,
            payload_json text not null
        )
        """
    )
    con.execute(
        """
        create table if not exists snapshots(
            id integer primary key autoincrement,
            indicator_code text not null,
            indicator_name text not null,
            value_toman integer,
            source_count integer not null,
            ok_count integer not null,
            stale_count integer not null,
            window_seconds integer not null,
            method text not null,
            created_at_utc text not null,
            created_at_tehran text not null,
            created_at_jalali text not null,
            created_time_iran text not null,
            payload_json text not null
        )
        """
    )
    con.execute(
        """
        create table if not exists derived_signals(
            id integer primary key autoincrement,
            signal_code text not null,
            signal_name text not null,
            value_json text not null,
            created_at_utc text not null,
            created_at_tehran text not null,
            created_at_jalali text not null
        )
        """
    )
    con.execute("create index if not exists idx_obs_indicator_time on observations(indicator_code, observed_at_utc)")
    con.execute("create index if not exists idx_obs_source_time on observations(source_code, observed_at_utc)")
    con.execute("create index if not exists idx_snap_indicator_time on snapshots(indicator_code, created_at_utc)")
    con.commit()
    return con


def sync_config_to_db(db_path: str, config: dict):
    con = ensure_db(db_path)
    stamp = jalali_stamp()["utc"]
    for ind in config.get("indicators", []):
        con.execute(
            "insert or replace into indicators(code,name,unit,category,config_json,updated_at) values(?,?,?,?,?,?)",
            (ind["code"], ind["name"], ind.get("unit", "toman"), ind.get("category"), json.dumps(ind, ensure_ascii=False), stamp),
        )
        for src in ind.get("sources", []):
            con.execute(
                """
                insert or replace into sources(code,indicator_code,name,url,channel,price_kind,input_unit,enabled,priority,weight,poll_interval_seconds,config_json,updated_at)
                values(?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    src["code"], ind["code"], src["name"], src["url"], src.get("channel", "website"), src.get("price_kind", "current"),
                    src.get("unit", "toman"), 1 if src.get("enabled", True) else 0, int(src.get("priority", 100)), float(src.get("weight", 1)),
                    int(src.get("poll_interval_seconds", config.get("collector", {}).get("default_poll_interval_seconds", 60))),
                    json.dumps(src, ensure_ascii=False), stamp,
                ),
            )
    con.commit()
    con.close()


def save_results(db_path: str, results: list[SourceResult], snapshots: list[dict]):
    con = ensure_db(db_path)
    for r in results:
        con.execute(
            """
            insert into observations(indicator_code,source_code,price_kind,value_toman,raw_value,ok,quality_score,latency_ms,error,observed_at_utc,observed_at_tehran,observed_at_jalali,observed_time_iran,payload_json)
            values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                r.indicator_code, r.source_code, r.price_kind, r.value_toman, r.raw_value, 1 if r.ok else 0, r.quality_score, r.latency_ms, r.error,
                r.observed_at_utc, r.observed_at_tehran, r.observed_at_jalali, r.observed_time_iran, json.dumps(asdict(r), ensure_ascii=False),
            ),
        )
    for s in snapshots:
        con.execute(
            """
            insert into snapshots(indicator_code,indicator_name,value_toman,source_count,ok_count,stale_count,window_seconds,method,created_at_utc,created_at_tehran,created_at_jalali,created_time_iran,payload_json)
            values(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                s["indicator_code"], s["indicator_name"], s.get("value_toman"), s["source_count"], s["ok_count"], s["stale_count"], s["window_seconds"],
                s["method"], s["created_at_utc"], s["created_at_tehran"], s["created_at_jalali"], s["created_time_iran"], json.dumps(s, ensure_ascii=False),
            ),
        )
    con.commit()
    con.close()


def _latest_good_by_source(results: list[SourceResult]) -> dict[str, SourceResult]:
    latest: dict[str, SourceResult] = {}
    for r in results:
        if not r.ok or r.value_toman is None:
            continue
        latest[r.source_code] = r
    return latest


def build_snapshots(config: dict, results: list[SourceResult]) -> list[dict]:
    quality = config.get("quality", {})
    method = quality.get("aggregation_method", "median")
    window_seconds = int(quality.get("freshness_window_seconds", 900))
    snapshots = []
    for ind in config.get("indicators", []):
        group = [r for r in results if r.indicator_code == ind["code"]]
        good = [r.value_toman for r in group if r.ok and r.value_toman is not None]
        if method == "mean" and good:
            value = round(statistics.mean(good))
        elif good:
            value = round(statistics.median(good))
        else:
            value = None
        stamp = jalali_stamp()
        snapshots.append(
            {
                "indicator_code": ind["code"],
                "indicator_name": ind["name"],
                "unit": "toman",
                "value_toman": value,
                "source_count": len(group),
                "ok_count": len(good),
                "stale_count": 0,
                "window_seconds": window_seconds,
                "method": method,
                "created_at_utc": stamp["utc"],
                "created_at_tehran": stamp["gregorian"],
                "created_at_jalali": stamp["jalali_date"],
                "created_time_iran": stamp["iran_time"],
                "sources": [asdict(r) for r in group],
            }
        )
    return snapshots


def _flatten_enabled_sources(config: dict) -> list[tuple[dict, dict]]:
    pairs = []
    for ind in config.get("indicators", []):
        for src in ind.get("sources", []):
            if src.get("enabled", True):
                pairs.append((ind, src))
    return pairs


def run_once(config_path: str = "configs/indicators.json") -> dict:
    cfg = load_config(config_path)
    app = cfg.get("app", {})
    db_path = app.get("sqlite_path", "data/market_data.db")
    sync_config_to_db(db_path, cfg)
    pairs = _flatten_enabled_sources(cfg)
    max_workers = int(cfg.get("collector", {}).get("max_workers", min(16, max(1, len(pairs)))))
    results: list[SourceResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {pool.submit(extract_source, ind, src, app): (ind, src) for ind, src in pairs}
        for fut in as_completed(future_map):
            results.append(fut.result())
    snapshots = build_snapshots(cfg, results)
    save_results(db_path, results, snapshots)
    payload = {"meta": {"project": "afra_market_data", "generated_at": jalali_stamp(), "source_count": len(results)}, "snapshots": snapshots}
    out_dir = Path(app.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest_payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def post_to_afra(payload: dict, config: dict) -> tuple[bool, str]:
    sync = config.get("sync", {})
    if not sync.get("enabled"):
        return False, "sync disabled"
    url = os.getenv("AFRA_API_URL") or sync.get("api_url")
    token = os.getenv("AFRA_API_TOKEN") or sync.get("api_token")
    if not url or str(url).startswith("${"):
        return False, "AFRA_API_URL is empty"
    headers = {"Content-Type": "application/json"}
    if token and not str(token).startswith("${"):
        headers["Authorization"] = f"Bearer {token}"
    r = requests.post(url, json=payload, headers=headers, timeout=sync.get("timeout_seconds", 30))
    return r.ok, f"{r.status_code} {r.text[:300]}"


def latest_rows(db_path: str = "data/market_data.db", limit: int = 250) -> list[dict]:
    if not Path(db_path).exists():
        return []
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute("select * from observations order by id desc limit ?", (limit,)).fetchall()
    con.close()
    return [dict(x) for x in rows]


def latest_snapshots(db_path: str = "data/market_data.db") -> list[dict]:
    if not Path(db_path).exists():
        return []
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        select s.* from snapshots s
        join (select indicator_code, max(id) max_id from snapshots group by indicator_code) x on x.max_id=s.id
        order by s.indicator_code
        """
    ).fetchall()
    con.close()
    out = []
    for row in rows:
        d = dict(row)
        try:
            d["payload"] = json.loads(d.pop("payload_json"))
        except Exception:
            pass
        out.append(d)
    return out


def live_payload(db_path: str = "data/market_data.db") -> dict:
    stamp = jalali_stamp()
    return {"server_time": stamp, "snapshots": latest_snapshots(db_path), "recent_observations": latest_rows(db_path, 50)}


def changed_sources(indicator_code: str, updated_within_minutes: int, compare_minutes: int, db_path: str = "data/market_data.db") -> list[dict]:
    if not Path(db_path).exists():
        return []
    cutoff = (now_utc() - timedelta(minutes=updated_within_minutes)).isoformat()
    compare_cutoff = (now_utc() - timedelta(minutes=compare_minutes)).isoformat()
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    latest = con.execute(
        """
        select o.* from observations o
        join (select source_code, max(id) max_id from observations where indicator_code=? and ok=1 and observed_at_utc>=? group by source_code) x on x.max_id=o.id
        """,
        (indicator_code, cutoff),
    ).fetchall()
    output = []
    for row in latest:
        prev = con.execute(
            """
            select * from observations where indicator_code=? and source_code=? and ok=1 and observed_at_utc<=? order by observed_at_utc desc limit 1
            """,
            (indicator_code, row["source_code"], compare_cutoff),
        ).fetchone()
        if not prev:
            continue
        delta = (row["value_toman"] or 0) - (prev["value_toman"] or 0)
        if delta != 0:
            output.append({"source_code": row["source_code"], "latest_value_toman": row["value_toman"], "previous_value_toman": prev["value_toman"], "delta_toman": delta, "latest_at": row["observed_at_tehran"], "previous_at": prev["observed_at_tehran"]})
    con.close()
    return output
