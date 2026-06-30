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
    title_lower = title.lower()
    if any(w in title_lower for w in ["یخچال", "لباسشویی", "ماشین ظرفشویی"]):
        return "لوازم خانگی"
    if any(w in title_lower for w in ["کولر", "هواساز", "تهویه"]):
        return "تهویه مطبوع"
    if any(w in title_lower for w in ["مبل", "کاناپه", "میز"]):
        return "مبلمان"
    return "محصولات"
