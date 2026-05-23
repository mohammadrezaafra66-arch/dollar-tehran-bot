# app/utils.py
import re
import time
import random
import logging
from app.config import Config
from playwright.sync_api import Page
from typing import Optional

# شماره‌های نامعتبر (placeholder)
INVALID_PHONES = [
    '00000001490', '09999999776', '06162922139', '000000014901',
    '02045495886', '06452020320', '05407725214', '00074420157',
    '00544077806', '00611837084', '00420989416', '00155619241',
    '00999999977', '00999999977'
]
# تنظیم logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# لاگ مخصوص خطاها
error_logger = logging.getLogger('errors')
error_handler = logging.FileHandler(Config.ERROR_LOG_FILE, encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)

def log_info(message: str):
    """لاگ اطلاعات عادی"""
    logging.info(message)

def log_error(message: str):
    """لاگ خطا"""
    error_logger.error(message)

# ... بقیه توابع همان‌طور که هست ...
def is_valid_phone(phone: str) -> bool:
    """بررسی معتبر بودن شماره ایران"""
    if not phone:
        return False
    
    phone = re.sub(r'[\s\-]', '', phone)
    
    if phone in INVALID_PHONES:
        return False
    
    # موبایل: 09xxxxxxxxx (11 رقم)
    if phone.startswith('09') and len(phone) == 11:
        return True
    
    # خط ثابت: 0xxxxxxxxxx (11 رقم)
    if phone.startswith('0') and len(phone) == 11:
        return True
    
    return False

def extract_phone(page: Page) -> str:
    """استخراج شماره تلفن از صفحه"""
    try:
        # روش 1: لینک tel:
        tel_link = page.locator('a[href^="tel:"]').first
        if tel_link.count() > 0:
            href = tel_link.get_attribute("href")
            if href:
                phone = re.sub(r"tel:", "", href)
                phone = re.sub(r"[\s\-]", "", phone)
                if is_valid_phone(phone):
                    return phone
        
        # روش 2: جستجوی مستقیم در صفحه
        content = page.content()
        patterns = [r'09\d{9}', r'0\d{10}']
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for phone in matches:
                if is_valid_phone(phone):
                    return phone
    except:
        pass
    
    return ""

def extract_website(page: Page) -> str:
    """استخراج وبسایت از صفحه"""
    try:
        link = page.locator('a[data-item-id="authority"]').first
        if link.count() > 0:
            href = link.get_attribute("href")
            if href and "google.com" not in href and "tel:" not in href:
                return href
    except:
        pass
    return ""

def extract_address(page: Page) -> str:
    """استخراج آدرس از صفحه"""
    try:
        addr_btn = page.locator('button[data-item-id="address"]').first
        if addr_btn.count() > 0:
            return addr_btn.text_content()[:200] or ""
    except:
        pass
    return ""

def extract_rating(page: Page) -> str:
    """استخراج امتیاز از صفحه"""
    try:
        rating = page.locator('div[aria-label*="star"]').first
        if rating.count() > 0:
            text = rating.get_attribute('aria-label')
            match = re.search(r'(\d+(?:\.\d+)?)', text)
            if match:
                return match.group(1)
    except:
        pass
    return ""

def extract_reviews_count(page: Page) -> str:
    """استخراج تعداد نظرات از صفحه"""
    try:
        reviews = page.locator('button[aria-label*="review"]').first
        if reviews.count() > 0:
            text = reviews.text_content()
            match = re.search(r'(\d+)', text)
            if match:
                return match.group(1)
    except:
        pass
    return ""

def extract_place_id_from_url(url: str) -> str:
    """استخراج Place ID از URL گوگل مپ"""
    match = re.search(r'!1s([^!]+)', url)
    if match:
        return match.group(1)
    return ""

def accept_cookies(page: Page) -> bool:
    """Accept کردن کوکی‌های گوگل"""
    try:
        time.sleep(1)
        selectors = [
            'button:has-text("Accept all")',
            'button:has-text("Accept")',
            'button[jsname="Njthtb"]',
            'form button',
        ]
        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible(timeout=1500):
                    btn.click()
                    print("  🍪 Cookies accepted")
                    time.sleep(1.5)
                    return True
            except:
                continue
        return False
    except:
        return False

def human_delay(min_sec: float = 1.0, max_sec: float = 2.0) -> None:
    """تأخیر تصادفی شبه انسان"""
    time.sleep(random.uniform(min_sec, max_sec))

def random_scroll_amount() -> int:
    """مقدار اسکرول تصادفی"""
    return random.randint(500, 1200)