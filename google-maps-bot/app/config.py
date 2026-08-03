# app/config.py - اضافه کردن LOG_FILE و ERROR_LOG_FILE

import os
import pandas as pd
from dataclasses import dataclass, field
from typing import Tuple, Optional


@dataclass
class Config:
    # ========== مسیرها ==========
    BASE_DIR: str = os.path.dirname(os.path.dirname(__file__))
    INPUT_DIR: str = os.path.join(BASE_DIR, 'input')
    OUTPUT_DIR: str = os.path.join(BASE_DIR, 'output')
    DATA_DIR: str = os.path.join(BASE_DIR, 'data')
    LOGS_DIR: str = os.path.join(BASE_DIR, 'logs')
    SCREENSHOTS_DIR: str = os.path.join(BASE_DIR, 'screenshots')
    
    # ========== فایل مدیریت ==========
    MANAGEMENT_FILE: str = os.path.join(INPUT_DIR, 'google_maps_management.xlsx')
    QUERIES_FILE: str = os.path.join(INPUT_DIR, 'google_maps_input.xlsx')
    
    # ========== فایل‌های دیتابیس ==========
    DATABASE_PATH: str = os.path.join(DATA_DIR, 'google_maps.db')
    CHECKPOINT_FILE: str = os.path.join(DATA_DIR, 'checkpoints', 'checkpoint.json')
    
    # ========== فایل‌های لاگ (اضافه کن) ==========
    LOG_FILE: str = os.path.join(LOGS_DIR, 'app.log')
    ERROR_LOG_FILE: str = os.path.join(LOGS_DIR, 'errors.log')
    
    # ========== تنظیمات پیش‌فرض ==========
    MAX_SCROLLS: int = 15
    MAX_BUSINESSES_PER_QUERY: int = 50
    MAX_BUSINESSES_TO_EXTRACT: int = 50
    MAX_WEBSITES_TO_CRAWL: int = 20
    HEADLESS: bool = False
    SLOW_MO: int = 500
    WEBSITE_CRAWL_ENABLED: bool = True
    EXTRACT_EMAILS: bool = True
    EXTRACT_SOCIAL: bool = True
    
    # تأخیرها
    DELAY_BETWEEN_BUSINESSES: Tuple[float, float] = (5.0, 10.0)
    DELAY_BETWEEN_QUERIES: Tuple[float, float] = (30.0, 60.0)
    DELAY_BETWEEN_SCROLLS: Tuple[float, float] = (3.0, 5.0)
    
    # ========== تنظیمات Chrome Profile ==========
    USE_CHROME_PROFILE: bool = os.getenv("USE_CHROME_PROFILE", "false").lower() in {"1", "true", "yes", "on"}
    USER_DATA_DIR: str = os.getenv("CHROME_USER_DATA_DIR", "")
    PROFILE_NAME: str = os.getenv("CHROME_PROFILE_NAME", "Default")

    # عمومی
    MISTAKE_RATE: float = 0.02
    HUMAN_LIKE_TYPING: bool = True
    PAGE_TIMEOUT: int = 45000
    CAPTCHA_API_KEY: str = ""
    
    @classmethod
    def create_directories(cls):
        """ایجاد پوشه‌های مورد نیاز"""
        for dir_path in [
            cls.INPUT_DIR, cls.OUTPUT_DIR, cls.DATA_DIR,
            cls.LOGS_DIR, cls.SCREENSHOTS_DIR
        ]:
            os.makedirs(dir_path, exist_ok=True)
        
        # پوشه checkpoints داخل data
        checkpoint_dir = os.path.join(cls.DATA_DIR, 'checkpoints')
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    @classmethod
    def load_from_excel(cls):
        """بارگذاری تنظیمات از فایل Excel مدیریت"""
        if not os.path.exists(cls.MANAGEMENT_FILE):
            print(f"⚠️ Management file not found: {cls.MANAGEMENT_FILE}")
            print("   Using default settings")
            cls.create_management_template()
            return
        
        try:
            df = pd.read_excel(cls.MANAGEMENT_FILE, sheet_name='Config')
            settings = dict(zip(df['Setting'], df['Value']))
            
            if 'max_scrolls' in settings:
                cls.MAX_SCROLLS = int(settings['max_scrolls'])
            if 'max_businesses_per_query' in settings:
                cls.MAX_BUSINESSES_PER_QUERY = int(settings['max_businesses_per_query'])
            if 'max_businesses_to_extract' in settings:
                cls.MAX_BUSINESSES_TO_EXTRACT = int(settings['max_businesses_to_extract'])
            if 'max_websites_to_crawl' in settings:
                cls.MAX_WEBSITES_TO_CRAWL = int(settings['max_websites_to_crawl'])
            if 'headless' in settings:
                cls.HEADLESS = str(settings['headless']).upper() == 'TRUE'
            if 'slow_mo' in settings:
                cls.SLOW_MO = int(settings['slow_mo'])
            if 'website_crawl_enabled' in settings:
                cls.WEBSITE_CRAWL_ENABLED = str(settings['website_crawl_enabled']).upper() == 'TRUE'
            
            if 'delay_between_businesses' in settings:
                delay_range = str(settings['delay_between_businesses']).split('-')
                if len(delay_range) == 2:
                    cls.DELAY_BETWEEN_BUSINESSES = (float(delay_range[0]), float(delay_range[1]))
            
            print("✅ Settings loaded from management Excel")
            
        except Exception as e:
            print(f"⚠️ Error loading management file: {e}")
            print("   Using default settings")
    
    @classmethod
    def create_management_template(cls):
        """ایجاد فایل مدیریت نمونه"""
        os.makedirs(cls.INPUT_DIR, exist_ok=True)
        
        config_data = {
            'Setting': [
                'max_scrolls',
                'max_businesses_per_query',
                'max_businesses_to_extract',
                'max_websites_to_crawl',
                'headless',
                'slow_mo',
                'website_crawl_enabled',
                'extract_emails',
                'extract_social',
                'delay_between_businesses',
                'delay_between_queries'
            ],
            'Value': [
                15, 50, 50, 20, 'FALSE', 500, 'TRUE', 'TRUE', 'TRUE', '5-10', '30-60'
            ],
            'Description': [
                'تعداد اسکرول در maps_collector',
                'حداکثر بیزینس در هر کوئری',
                'حداکثر بیزینس برای استخراج جزئیات',
                'حداکثر وبسایت برای کرال',
                'حالت headless مرورگر',
                'تأخیر بین اکشن‌ها (میلی‌ثانیه)',
                'فعال/غیرفعال کردن کرالر وبسایت',
                'استخراج ایمیل از وبسایت‌ها',
                'استخراج شبکه‌های اجتماعی',
                'تأخیر بین بیزینس‌ها (ثانیه)',
                'تأخیر بین کوئری‌ها (ثانیه)'
            ]
        }
        
        df_config = pd.DataFrame(config_data)
        
        phases_data = {
            'Phase': ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'],
            'Name': ['Query Generator', 'Maps Collector', 'Business Extractor', 'Website Crawler'],
            'Enabled': [True, True, True, True],
            'Description': [
                'تولید کوئری‌ها از Excel',
                'جمع‌آوری بیزینس‌ها از گوگل مپ',
                'استخراج جزئیات از گوگل مپ',
                'کرال کردن وبسایت‌ها'
            ]
        }
        
        df_phases = pd.DataFrame(phases_data)
        
        with pd.ExcelWriter(cls.MANAGEMENT_FILE, engine='openpyxl') as writer:
            df_config.to_excel(writer, sheet_name='Config', index=False)
            df_phases.to_excel(writer, sheet_name='Phases', index=False)
        
        print(f"✅ Created management template: {cls.MANAGEMENT_FILE}")
    
    @classmethod
    def is_phase_enabled(cls, phase_name: str) -> bool:
        """بررسی فعال بودن یک فاز"""
        if not os.path.exists(cls.MANAGEMENT_FILE):
            return True
        
        try:
            df = pd.read_excel(cls.MANAGEMENT_FILE, sheet_name='Phases')
            phase_row = df[df['Name'] == phase_name]
            if not phase_row.empty:
                return bool(phase_row.iloc[0]['Enabled'])
        except:
            pass
        return True
    @classmethod
    def is_execution_allowed(cls) -> bool:
        """بررسی آیا در زمان فعلی مجاز به اجرا هستیم"""
        import jdatetime
        from datetime import datetime
        
        # خواندن از management.xlsx
        if not os.path.exists(cls.MANAGEMENT_FILE):
            return True  # اگر فایل نبود، اجازه بده
        
        try:
            import pandas as pd
            df = pd.read_excel(cls.MANAGEMENT_FILE, sheet_name='Config')
            settings = dict(zip(df['تنظیمات'], df['مقدار']))
            
            # ساعت شروع و پایان
            start_time = settings.get('🕐 ساعت شروع', '08:00')
            end_time = settings.get('🕐 ساعت پایان', '23:00')
            current_time = datetime.now().strftime('%H:%M')
            
            if current_time < start_time or current_time > end_time:
                print(f"⏸️ Outside execution window ({start_time}-{end_time})")
                return False
            
            # وضعیت Pause/Resume
            status = settings.get('⏸️ وضعیت Pause/Resume', 'resume')
            if status.lower() == 'pause':
                print("⏸️ System is paused (status=pause)")
                return False
            
            # روزهای اجرا
            days_str = settings.get('📆 روزهای اجرا', '')
            if days_str:
                allowed_days = [d.strip() for d in days_str.split(',')]
                # تبدیل روز جاری به فارسی
                persian_days = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
                today_persian = persian_days[datetime.now().weekday() + 1]
                if today_persian not in allowed_days:
                    print(f"⏸️ Today ({today_persian}) is not in allowed days")
                    return False
            
            # تاریخ شمسی (اختیاری)
            start_date_shamsi = settings.get('📅 تاریخ شروع (شمسی)', '')
            end_date_shamsi = settings.get('📅 تاریخ پایان (شمسی)', '')
            if start_date_shamsi and end_date_shamsi:
                try:
                    start_date = jdatetime.datetime.strptime(start_date_shamsi, '%Y-%m-%d').date()
                    end_date = jdatetime.datetime.strptime(end_date_shamsi, '%Y-%m-%d').date()
                    today_shamsi = jdatetime.date.today()
                    
                    if today_shamsi < start_date or today_shamsi > end_date:
                        print(f"⏸️ Outside date range ({start_date_shamsi} to {end_date_shamsi})")
                        return False
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error checking execution policy: {e}")
            return True  # در صورت خطا، اجازه بده اجرا شود
# ایجاد پوشه‌ها هنگام بارگذاری
Config.create_directories()

# بارگذاری تنظیمات
Config.load_from_excel()