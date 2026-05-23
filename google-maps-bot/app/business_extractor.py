# app/business_extractor.py - نسخه به‌روز شده با Config
from playwright.sync_api import sync_playwright
import time
import json
import random
from datetime import datetime
import os
from app.config import Config
from app.utils import extract_phone, extract_website, extract_address, accept_cookies
from app.database import Database

print("Database path:", Config.DATABASE_PATH)

def is_page_valid(page):
    """بررسی اینکه صفحه واقعاً محتوای مفید دارد (با تشخیص قطع نت)"""
    try:
        # روش ۱: بررسی وجود جعبه جستجو
        search_box = page.locator('[role="combobox"]').first
        if search_box.count() > 0 and search_box.is_visible():
            return True
        
        # روش ۲: بررسی وجود پنل اطلاعات
        panel = page.locator('[role="main"]').first
        if panel.count() > 0 and panel.is_visible():
            return True
        
        # روش ۳: بررسی URL
        current_url = page.url
        if '/place/' not in current_url:
            print(f"  ⚠️ Not on a business page")
            return False
        
        # روش ۴: بررسی متن صفحه برای خطاهای قطع نت
        content = page.content().lower()
        
        error_keywords = [
            'err_name_not_resolved',
            'err_connection_refused',
            'err_connection_timed_out',
            'err_internet_disconnected',
            'unable to connect',
            'no internet',
            'this site can\'t be reached',
            'dns_probe_finished_no_internet',
        ]
        
        for keyword in error_keywords:
            if keyword in content:
                print(f"  ⚠️ Network error detected: {keyword}")
                return False
        
        # روش ۵: بررسی حداقل محتوای مفید
        if len(content) < 1000:
            print(f"  ⚠️ Page too small: {len(content)} chars")
            return False
        
        # روش ۶: بررسی وجود دکمه تلفن یا آدرس
        has_phone_btn = page.locator('a[href^="tel:"]').count() > 0
        has_address_btn = page.locator('button[data-item-id="address"]').count() > 0
        
        if not has_phone_btn and not has_address_btn:
            print(f"  ⚠️ No phone or address button found")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ⚠️ Error checking page validity: {e}")
        return False

def detect_captcha(page):
    try:
        content = page.content().lower()
        captcha_keywords = ['captcha', 'unusual traffic', 'verify you are human']
        for keyword in captcha_keywords:
            if keyword in content:
                return True
        return False
    except:
        return False

def extract_businesses(
    input_file=None,
    output_file='output/phase4_result.json',
    max_businesses=None,
    use_profile=False,
    user_data_dir=None,
    profile_name=None
):
    """
    استخراج جزئیات بیزینس‌ها از گوگل مپ
    
    Args:
        max_businesses: اگر None باشد از Config.MAX_BUSINESSES_TO_EXTRACT استفاده می‌کند
    """
    print("=" * 60)
    print("📍 Extracting business details (Unlimited Loop with Retry)")
    print("=" * 60)
    
    # اگر max_businesses مشخص نشده، از Config بگیر
    if max_businesses is None:
        max_businesses = Config.MAX_BUSINESSES_TO_EXTRACT
        print(f"📋 Using max_businesses from Config: {max_businesses}")
    
    db = Database()
    stats = db.get_stats()
    print(f"📊 DB Stats BEFORE: Total={stats['total']}, Done={stats['done']}, Failed={stats['failed']}")
    
    round_number = 0
    total_processed = 0
    
    while True:
        round_number += 1
        print(f"\n{'='*40}")
        print(f"🔄 ROUND {round_number}: Fetching next batch")
        print(f"{'='*40}")
        
        # دریافت دسته بعدی (اولویت با failedها)
        businesses_to_process = db.get_next_business_for_processing(limit=max_businesses)
        
        if not businesses_to_process:
            print("✅ No more pending or retryable failed businesses")
            break
        
        print(f"📋 Processing {len(businesses_to_process)} businesses...")
        
        with sync_playwright() as p:
            # استفاده از تنظیمات Config
            browser = p.chromium.launch(
                headless=Config.HEADLESS,
                slow_mo=Config.SLOW_MO
            )
            page = browser.new_page()
            accept_cookies(page)
            
            for biz in businesses_to_process:
                total_processed += 1
                retry_info = f" (retry {biz.get('retry_count', 0)}/3)" if biz.get('retry_count', 0) > 0 else ""
                print(f"\n🔍 [{total_processed}] {biz['name'][:50]}...{retry_info}")
                
                has_error = False
                error_message = None
                phone = website = address = ""
                
                try:
                    print(f"  🌐 Navigating to page...")
                    response = page.goto(biz['clean_href'], wait_until="domcontentloaded", timeout=Config.PAGE_TIMEOUT)
                    
                    if response and response.status >= 400:
                        has_error = True
                        error_message = f"HTTP {response.status}"
                    else:
                        print(f"  ✅ Page loaded, checking content...")
                        time.sleep(2)
                        
                        if not is_page_valid(page):
                            has_error = True
                            error_message = "Page loaded but no valid content (network issue?)"
                        elif detect_captcha(page):
                            print(f"  🤖 Captcha detected!")
                            page.screenshot(path=f"screenshots/captcha_{total_processed}.png")
                            has_error = True
                            error_message = 'CAPTCHA'
                        else:
                            phone = extract_phone(page)
                            website = extract_website(page)
                            address = extract_address(page)
                            
                            if phone:
                                print(f"  📞 {phone}")
                            if website:
                                print(f"  🌐 {website}")
                            
                except Exception as e:
                    has_error = True
                    error_message = f"{type(e).__name__}: {str(e)[:100]}"
                    print(f"  ❌ Exception: {error_message}")
                
                if has_error:
                    db.mark_failed(biz['id'], error_message)
                    print(f"  📝 DB: marked FAILED (will retry later)")
                else:
                    db.mark_success(biz['id'], phone, website, address)
                    print(f"  📝 DB: marked SUCCESS")
                
                # نمایش پیشرفت
                stats = db.get_stats()
                print(f"  📊 Progress: Done={stats['done']}, Failed={stats['failed']}, Pending={stats['pending']}")
                
                # استفاده از تأخیر از Config
                min_delay, max_delay = Config.DELAY_BETWEEN_BUSINESSES
                time.sleep(random.uniform(min_delay, max_delay))
            
            browser.close()
    
    # آمار نهایی
    stats = db.get_stats()
    print("\n" + "=" * 60)
    print("✅ ALL EXTRACTION COMPLETED!")
    print(f"📊 Final Stats: Total={stats['total']}, Done={stats['done']}, Failed={stats['failed']}")
    print(f"📞 Phone: {stats['phones']}, 🌐 Website: {stats['websites']}")
    print("=" * 60)
    
    # گرفتن نتایج موفق برای خروجی Excel
    results = db.get_all_done_businesses()
    
    # ذخیره JSON برای سازگاری با exporter قدیم
    output = {
        'total': len(results),
        'businesses': results,
        'timestamp': datetime.now().isoformat()
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    db.close()
    return results

if __name__ == "__main__":
    os.makedirs('output', exist_ok=True)
    os.makedirs('screenshots', exist_ok=True)
    # حالا از Config.MAX_BUSINESSES_TO_EXTRACT استفاده می‌کند
    extract_businesses()