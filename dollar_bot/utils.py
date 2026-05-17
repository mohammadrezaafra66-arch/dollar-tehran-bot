from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


JALALI_WEEKDAYS = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621

    gy2 = gy + 1 if gm > 2 else gy
    days = (
        365 * gy
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        - 80
        + gd
        + g_d_m[gm - 1]
    )

    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365

    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30

    return jy, jm, jd


def format_jalali_datetime(dt: datetime) -> str:
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    weekday = JALALI_WEEKDAYS[dt.weekday()]
    return f"{jy:04d}/{jm:02d}/{jd:02d} - {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} - {weekday}"


def now_iso(tz_name: str = "Asia/Tehran") -> str:
    # نام این تابع برای سازگاری با کد قبلی عوض نشده، اما خروجی از این به بعد شمسی و ساعت ایران است.
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone(timedelta(hours=3, minutes=30))
    return format_jalali_datetime(datetime.now(tz))


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
