from __future__ import annotations

from pathlib import Path

DEFAULT_TEMPLATE = """سلام {name} عزیز،

آگهی شما رو در دیوار دیدم. ما در افراکالا با قیمت‌های رقابتی {category} داریم.
اگر مایل به همکاری هستید خوشحال می‌شیم بیشتر صحبت کنیم.

با تشکر
تیم افراکالا"""


def load_template(path: str | None = None) -> str:
    candidate = Path(path or "") if path else None
    if candidate and candidate.exists():
        return candidate.read_text(encoding="utf-8")
    template_path = Path(__file__).resolve().parents[1] / "data" / "message_template.txt"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return DEFAULT_TEMPLATE


def save_template(template: str, path: str | None = None) -> str:
    target = Path(path or "") if path else Path(__file__).resolve().parents[1] / "data" / "message_template.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template, encoding="utf-8")
    return str(target)


def build_message(lead: dict, template: str | None = None) -> str:
    tpl = template or load_template()
    name = lead.get("seller_name", "").strip() or "فروشنده گرامی"
    category = _guess_category(lead.get("title", ""))
    return tpl.format(
        name=name,
        category=category,
        city=lead.get("city", ""),
        title=lead.get("title", ""),
    )


def _guess_category(title: str) -> str:
    title_lower = (title or "").lower()
    if any(w in title_lower for w in ["اسپیکر", "بلندگو", "هدفون", "هدست", "speaker"]):
        return "اسپیکر و صوتی"
    if any(w in title_lower for w in ["تلویزیون", "مانیتور", "پروژکتور", "led", "lcd"]):
        return "تلویزیون و نمایش"
    if any(w in title_lower for w in ["آمپلی‌فایر", "آمپلیفایر", "پاور", "میکسر", "mixer"]):
        return "آمپلی‌فایر و تجهیزات صوتی"
    if any(w in title_lower for w in ["هوم تیاتر", "home theater", "ساندبار", "soundbar"]):
        return "هوم تیاتر"
    if any(w in title_lower for w in ["دوربین", "دی‌وی‌آر", "dvr", "nvr"]):
        return "دوربین و سیستم امنیتی"
    return "تجهیزات صوتی و تصویری"
