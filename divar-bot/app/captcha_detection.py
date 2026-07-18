"""تشخیص صفحات captcha و محدودیت دیوار."""

BLOCK_SIGNALS = [
    "تایید نیستم ربات",
    "captcha",
    "I'm not a robot",
    "محدودیت",
    "دسترسی محدود",
    "access denied",
]


def is_blocked(page_content: str) -> bool:
    text = (page_content or "").lower()
    return any(signal.lower() in text for signal in BLOCK_SIGNALS)


def detect_and_handle(page) -> bool:
    """True یعنی صفحه مسدود شده — False یعنی ادامه بده."""
    try:
        content = page.locator("body").inner_text(timeout=5000)
        return is_blocked(content)
    except Exception:
        return False
