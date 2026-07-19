DEFAULT_TEMPLATE = """سلام {name} عزیز،

آگهی شما رو در دیوار دیدم. ما در افراکالا با قیمت‌های رقابتی {category} داریم.
اگر مایل به همکاری هستید خوشحال می‌شیم بیشتر صحبت کنیم.

با تشکر
تیم افراکالا"""


def build_message(lead: dict, template: str = None) -> str:
    tpl = template or DEFAULT_TEMPLATE
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
