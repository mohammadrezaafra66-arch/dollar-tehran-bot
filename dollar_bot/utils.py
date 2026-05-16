from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo


def now_iso(tz_name: str = "Asia/Tehran") -> str:
    return datetime.now(ZoneInfo(tz_name)).isoformat(timespec="seconds")


def normalize_price_to_toman(raw: object) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    fa_digits = "۰۱۲۳۴۵۶۷۸۹"
    ar_digits = "٠١٢٣٤٥٦٧٨٩"
    for i, ch in enumerate(fa_digits):
        text = text.replace(ch, str(i))
    for i, ch in enumerate(ar_digits):
        text = text.replace(ch, str(i))

    numbers = re.findall(r"\d+(?:[,.\s]\d+)*", text)
    if not numbers:
        return None

    num_text = re.sub(r"[^0-9]", "", numbers[0])
    if not num_text:
        return None
    value = int(num_text)

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
