from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def now_iso(tz_name: str = "Asia/Tehran") -> str:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone(timedelta(hours=3, minutes=30))
    return datetime.now(tz).isoformat(timespec="seconds")


def _to_english_digits(text: str) -> str:
    fa_digits = "۰۱۲۳۴۵۶۷۸۹"
    ar_digits = "٠١٢٣٤٥٦٧٨٩"
    for i, ch in enumerate(fa_digits):
        text = text.replace(ch, str(i))
    for i, ch in enumerate(ar_digits):
        text = text.replace(ch, str(i))
    return text


def _clean_number(value: str) -> int | None:
    num_text = re.sub(r"[^0-9]", "", value or "")
    if not num_text:
        return None
    return int(num_text)


def normalize_price_to_toman(raw: object) -> int | None:
    if raw is None:
        return None
    text = _to_english_digits(str(raw).strip())
    if not text:
        return None

    # Examples:
    # 81 هزار => 81000 toman
    # 140 هزار و 308 تومان => 140308 toman
    # 1,403,080 ریال => 140308 toman
    thousand_match = re.search(r"(\d{2,4})\s*هزار(?:\s*و\s*(\d{1,3}))?", text)
    if thousand_match:
        major = int(thousand_match.group(1))
        minor = int(thousand_match.group(2) or 0)
        return major * 1000 + minor

    numbers = re.findall(r"\d+(?:[,.\s]\d+)*", text)
    if not numbers:
        return None

    value = _clean_number(numbers[0])
    if value is None:
        return None

    if "ریال" in text or "rial" in text.lower():
        value = round(value / 10)
    return value


def get_by_json_path(data: object, path: str) -> object | None:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            idx = int(part)
            current = current[idx] if 0 <= idx < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current


def calc_average(buy: int | None, sell: int | None, average: int | None) -> int | None:
    if average is not None:
        return average
    if buy is not None and sell is not None:
        return round((buy + sell) / 2)
    return sell if sell is not None else buy
