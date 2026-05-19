from __future__ import annotations

import copy
import json
import os
import re
import sqlite3
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
TEHRAN = timezone(timedelta(hours=3, minutes=30))

RANGES = {
    "usd_tehran": (10000, 1000000),
    "aed_tehran": (1000, 200000),
    "eur_tehran": (10000, 2000000),
    "xau_usd": (500, 10000),
    "sekkeh": (10000000, 1000000000),
    "geram18": (1000000, 100000000),
}


def now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def gregorian_to_jalali(gy: int, gm: int, gd: int):
    gdm = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + gdm[gm - 1]
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
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def jalali_stamp(dt: datetime | None = None) -> dict[str, str]:
    dt = dt or now_tehran()
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    return {
        "gregorian": dt.isoformat(),
        "jalali_date": f"{jy:04d}/{jm:02d}/{jd:02d}",
        "jalali_date_fa": f"{fa_num(jy)}/{fa_num(str(jm).zfill(2))}/{fa_num(str(jd).zfill(2))}",
        "iran_time": dt.strftime("%H:%M:%S"),
        "iran_time_fa": fa_num(dt.strftime("%H:%M:%S")),
    }


def clean_number(text: str) -> float:
    if text is None:
        raise ValueError("empty number")
    s = str(text).translate(FA_DIGITS)
    for ch in [",", "،", "٬", " ", "\u200e", "\u200f", "\xa0"]:
        s = s.replace(ch, "")
    match = re.search(r"-?\d+(?:\.\d+)?", s)
    if not match:
        raise ValueError(f"number not found in {text!r}")
    value = float(match.group(0))
    return int(value) if value.is_integer() else value


def normalize(value: float, unit: str) -> float:
    unit = (unit or "toman").lower()
    value = value / 10 if unit in ("rial", "irr") else value
    return int(value) if float(value).is_integer() else round(value, 6)


def validate_value(indicator_code: str, value: float, unit: str) -> None:
    bounds = RANGES.get((indicator_code or "").lower())
    if not bounds:
        return
    low, high = bounds
    if not (low <= float(value) <= high):
        raise ValueError(f"value out of expected range for {indicator_code}: {value} {unit}")


@dataclass
class SourceResult:
    indicator_code: str
    indicator_name: str
    source_code: str
    source_name: str
    price_kind: str
    url: str
    ok: bool
    value_toman: float | None
    raw_value: str | None
    input_unit: str
    error: str | None
    collected_at: str
    collected_at_jalali: str
    collected_time_iran: str


def _merge_extra_sources(config: dict, config_path: Path) -> dict:
    extra_path = config_path.parent / "extra_sources.json"
    if not extra_path.exists():
        return config
    merged = copy.deepcopy(config)
    extra = json.loads(extra_path.read_text(encoding="utf-8"))
    indicators = {item.get("code"): item for item in merged.setdefault("indicators", [])}
    for src in extra.get("sources", []):
        indicator_code = src.get("indicator_code")
        if not indicator_code:
            continue
        indicator = indicators.get(indicator_code)
        if not indicator:
            indicator = {
                "code": indicator_code,
                "name": src.get("indicator_name") or indicator_code,
                "unit": src.get("indicator_unit") or src.get("unit") or "unit",
                "sources": [],
            }
            merged["indicators"].append(indicator)
            indicators[indicator_code] = indicator
        clean_src = {k: v for k, v in src.items() if k not in ("indicator_code", "indicator_name", "indicator_unit")}
        codes = {s.get("code") for s in indicator.setdefault("sources", [])}
        if clean_src.get("code") not in codes:
            indicator["sources"].append(clean_src)
    return merged


def load_config(path: str = "configs/indicators.json") -> dict:
    config_path = Path(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return _merge_extra_sources(config, config_path)


def fetch_html(url: str, timeout: int, user_agent: str) -> str:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": user_agent, "Accept-Language": "fa,en;q=0.8"})
    response.raise_for_status()
    return response.text


def _non_empty(value: str, label: str) -> str:
    value = "" if value is None else str(value).strip()
    if not value:
        raise ValueError(f"{label} returned empty text")
    return value


def extract_by_step(page: str, step: dict) -> str:
    kind = step.get("kind")
    soup = BeautifulSoup(page, "html.parser")
    if kind == "css":
        element = soup.select_one(step["selector"])
        if not element:
            raise ValueError("css selector not found")
        return _non_empty(element.get_text(" ", strip=True), "css selector")
    if kind == "regex":
        match = re.search(step["pattern"], page, re.S)
        if not match:
            raise ValueError("regex not matched")
        return _non_empty(match.group(1) if match.groups() else match.group(0), "regex")
    if kind == "row_contains":
        words = step.get("contains", [])
        pattern = step.get("number_pattern", r"([0-9۰-۹٠-٩]{1,3}(?:[,،٬][0-9۰-۹٠-٩]{3})*(?:\.[0-9۰-۹٠-٩]+)?)")
        for row in soup.find_all(["tr", "div", "article"]):
            text = row.get_text(" ", strip=True)
            if all(word in text for word in words):
                numbers = re.findall(pattern, text)
                if numbers:
                    return _non_empty(numbers[int(step.get("index", 0))], "row_contains")
        raise ValueError("row with requested words not found")
    raise ValueError(f"unknown extractor kind: {kind}")


def extract_source(indicator: dict, source: dict, app: dict) -> SourceResult:
    stamp = jalali_stamp()
    base = dict(
        indicator_code=indicator["code"],
        indicator_name=indicator["name"],
        source_code=source["code"],
        source_name=source["name"],
        price_kind=source.get("price_kind", "current"),
        url=source["url"],
        input_unit=source.get("unit", "toman"),
        collected_at=stamp["gregorian"],
        collected_at_jalali=stamp["jalali_date"],
        collected_time_iran=stamp["iran_time"],
    )
    try:
        if source["url"].startswith("manual://"):
            raw = str(source["manual_value"])
        else:
            page = fetch_html(source["url"], app.get("timeout_seconds", 20), app.get("user_agent", "Mozilla/5.0"))
            raw = None
            last_error = None
            for step in source.get("extractors", []):
                try:
                    candidate = extract_by_step(page, step)
                    value_candidate = normalize(clean_number(candidate), source.get("unit", "toman"))
                    validate_value(indicator["code"], value_candidate, source.get("unit", "toman"))
                    raw = candidate
                    break
                except Exception as exc:
                    last_error = str(exc)
            if raw is None:
                raise ValueError(last_error or "no extractor matched")
        value = normalize(clean_number(raw), source.get("unit", "toman"))
        validate_value(indicator["code"], value, source.get("unit", "toman"))
        return SourceResult(**base, ok=True, value_toman=value, raw_value=raw, error=None)
    except Exception as exc:
        return SourceResult(**base, ok=False, value_toman=None, raw_value=None, error=f"{type(exc).__name__}: {exc}")


def ensure_db(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("""create table if not exists results(
        id integer primary key autoincrement,
        indicator_code text,
        source_code text,
        price_kind text,
        ok integer,
        value_toman real,
        raw_value text,
        error text,
        payload text,
        collected_at text
    )""")
    connection.execute("""create table if not exists snapshots(
        id integer primary key autoincrement,
        indicator_code text,
        indicator_name text,
        value_toman real,
        source_count integer,
        ok_count integer,
        payload text,
        created_at text
    )""")
    connection.commit()
    return connection


def save_results(db_path: str, results: list[SourceResult], snapshots: list[dict]) -> None:
    connection = ensure_db(db_path)
    for row in results:
        connection.execute(
            "insert into results(indicator_code,source_code,price_kind,ok,value_toman,raw_value,error,payload,collected_at) values(?,?,?,?,?,?,?,?,?)",
            (row.indicator_code, row.source_code, row.price_kind, 1 if row.ok else 0, row.value_toman, row.raw_value, row.error, json.dumps(asdict(row), ensure_ascii=False), row.collected_at),
        )
    for snap in snapshots:
        connection.execute(
            "insert into snapshots(indicator_code,indicator_name,value_toman,source_count,ok_count,payload,created_at) values(?,?,?,?,?,?,?)",
            (snap["indicator_code"], snap["indicator_name"], snap.get("value_toman"), snap["source_count"], snap["ok_count"], json.dumps(snap, ensure_ascii=False), snap["created_at"]),
        )
    connection.commit()
    connection.close()


def build_snapshots(config: dict, results: list[SourceResult]) -> list[dict]:
    snapshots = []
    for indicator in config.get("indicators", []):
        group = [row for row in results if row.indicator_code == indicator["code"]]
        good_values = [row.value_toman for row in group if row.ok and row.value_toman is not None]
        stamp = jalali_stamp()
        snapshots.append({
            "indicator_code": indicator["code"],
            "indicator_name": indicator["name"],
            "unit": indicator.get("unit", "unit"),
            "value_toman": statistics.median(good_values) if good_values else None,
            "source_count": len(group),
            "ok_count": len(good_values),
            "created_at": stamp["gregorian"],
            "created_at_jalali": stamp["jalali_date"],
            "created_time_iran": stamp["iran_time"],
            "sources": [asdict(row) for row in group],
        })
    return snapshots


def run_once(config_path: str = "configs/indicators.json") -> dict:
    config = load_config(config_path)
    app = config.get("app", {})
    results = []
    for indicator in config.get("indicators", []):
        for source in indicator.get("sources", []):
            if source.get("enabled", True):
                results.append(extract_source(indicator, source, app))
                time.sleep(app.get("sleep_between_sources_seconds", 0))
    snapshots = build_snapshots(config, results)
    save_results(app.get("sqlite_path", "data/market_data.db"), results, snapshots)
    payload = {"meta": {"project": "afra_market_data", "generated_at": jalali_stamp()}, "snapshots": snapshots}
    output_dir = Path(app.get("output_dir", "output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "latest_payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def post_to_afra(payload: dict, config: dict) -> tuple[bool, str]:
    sync = config.get("sync", {})
    if not sync.get("enabled"):
        return False, "sync disabled"
    url = os.getenv("AFRA_API_URL") or sync.get("api_url")
    token = os.getenv("AFRA_API_TOKEN") or sync.get("api_token")
    if not url:
        return False, "AFRA_API_URL is empty"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.post(url, json=payload, headers=headers, timeout=sync.get("timeout_seconds", 30))
    return response.ok, f"{response.status_code} {response.text[:300]}"


def latest_rows(db_path: str = "data/market_data.db", limit: int = 100):
    if not Path(db_path).exists():
        return []
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute("select * from results order by id desc limit ?", (limit,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]
