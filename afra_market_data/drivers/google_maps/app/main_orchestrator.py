# app/main_orchestrator.py - نسخه نهایی با Checkpoint + Execution Policy
import json
import os
from datetime import datetime
from app.maps_collector import collect_businesses
from app.business_extractor import extract_businesses
from app.excel_exporter import export_to_excel
from app.config import Config
from app.database import Database  
from app.query_generator import QueryGenerator
from app.website_crawler import WebsiteCrawler

class Orchestrator:
    """مدیر هماهنگ‌کننده اجرای کل پروژه با قابلیت چکپوینت و زمان‌بندی"""
    
    def __init__(self):
        self.results = []
        self.checkpoint_file = Config.CHECKPOINT_FILE
    
    def is_execution_allowed(self) -> bool:
        """بررسی آیا در زمان فعلی مجاز به اجرا هستیم (از google_maps_management.xlsx)"""
        management_file = Config.MANAGEMENT_FILE
        
        if not os.path.exists(management_file):
            return True
        
        try:
            import pandas as pd
            from datetime import datetime
            
            # خواندن از شیت Config
            df = pd.read_excel(management_file, sheet_name='Config')
            settings = dict(zip(df['Setting'], df['Value']))
            
            # ساعت شروع و پایان
            start_time_str = str(settings.get('start_time', '08:00')).strip()
            end_time_str = str(settings.get('end_time', '23:00')).strip()
            
            if ':' not in start_time_str:
                start_time_str = '08:00'
            if ':' not in end_time_str:
                end_time_str = '23:00'
            
            current_time_str = datetime.now().strftime('%H:%M')
            
            if current_time_str < start_time_str or current_time_str > end_time_str:
                print(f"⏸️ Outside execution window ({start_time_str}-{end_time_str})")
                return False
            
            # وضعیت Pause/Resume
            status = str(settings.get('pause_resume', 'resume')).lower()
            if status == 'pause':
                print("⏸️ System is paused (pause_resume=pause)")
                return False
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error checking execution policy: {e}")
            return True
    
    def load_queries_fallback(self):
        """بارگذاری کوئری‌ها از فایل JSON (fallback)"""
        input_file = os.path.join(Config.INPUT_DIR, 'queries.json')
        
        if not os.path.exists(input_file):
            print(f"⚠️ Fallback file not found: {input_file}")
            return []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            queries = json.load(f)
        
        search_queries = []
        for q in queries:
            keyword = q.get('keyword', '').strip()
            city = q.get('city', '').strip()
            if keyword and city:
                search_queries.append(f"{keyword} در {city}")
        
        return search_queries
    
    def save_checkpoint(self, query_index, total_queries, current_query):
        """ذخیره آخرین وضعیت اجرا"""
        checkpoint = {
            'last_query_index': query_index,
            'total_queries': total_queries,
            'current_query': current_query,
            'timestamp': datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        print(f"💾 Checkpoint saved: Query {query_index}/{total_queries}")
    
    def load_checkpoint(self):
        """بارگذاری آخرین وضعیت اجرا"""
        if not os.path.exists(self.checkpoint_file):
            return 0
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            start_index = checkpoint.get('last_query_index', 0)
            print(f"🔄 Resuming from checkpoint: Query {start_index + 1}")
            return start_index
        except:
            return 0
    
    def clear_checkpoint(self):
        """پاک کردن چکپوینت بعد از اتمام موفق"""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print("✅ Checkpoint cleared")
    
    def run(self):
        # ========== بررسی مجوز اجرا (زمان‌بندی) ==========
        if not self.is_execution_allowed():
            print("⏸️ Execution not allowed at this time. Exiting.")
            return
        
        # لاگ شروع اجرا
        log_line = f"{datetime.now().isoformat()} - Starting execution"
        os.makedirs('logs', exist_ok=True)
        with open('logs/execution.log', 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
        print(log_line)
        
        print("=" * 60)
        print("🚀 Google Maps Scraper - Professional Edition")
        print("=" * 60)
        
        # نمایش تنظیمات فعلی
        self._show_settings()
        
        # ========== مرحله ۱: تولید کوئری‌ها (فقط یکبار) ==========
        print("\n" + "=" * 60)
        print("📍 PHASE 1: Query Generator")
        print("=" * 60)
        
        generator = QueryGenerator()
        queries = generator.run()
        
        if not queries:
            print("⚠️ No queries generated from Excel, trying fallback...")
            queries = self.load_queries_fallback()
        
        if not queries:
            print("❌ No queries found! Please add data to input/google_maps_input.xlsx")
            return
        
        print(f"\n📋 Total queries to process: {len(queries)}")
        
        # ========== بارگذاری چکپوینت ==========
        start_index = self.load_checkpoint()
        
        # ========== فاز ۲ و ۳: برای هر کوئری ==========
        for idx in range(start_index, len(queries)):
            query = queries[idx]
            current_num = idx + 1
            
            print(f"\n{'='*60}")
            print(f"📍 PROCESSING QUERY [{current_num}/{len(queries)}]: {query}")
            print(f"{'='*60}")
            
            # ========== فاز ۲: جمع‌آوری بیزینس‌ها از گوگل مپ ==========
            print("\n🔍 PHASE 2: Maps Collector")
            businesses = collect_businesses(
                query, 
                max_scrolls=Config.MAX_SCROLLS,
                max_businesses=Config.MAX_BUSINESSES_PER_QUERY
            )
            
            if not businesses:
                print(f"⚠️ No businesses found for: {query}")
                self.save_checkpoint(current_num, len(queries), query)
                continue
            
            # ========== ذخیره در دیتابیس ==========
            print("\n💾 Saving to database...")
            db = Database()
            
            reset_count = db.reset_processing_to_pending()
            if reset_count > 0:
                print(f"🔄 Reset {reset_count} stuck processing jobs")
            
            db.add_businesses_batch(query, businesses)
            db.close()
            
            # ========== فاز ۳: استخراج جزئیات از گوگل مپ ==========
            print("\n📍 PHASE 3: Business Extractor")
            extract_businesses(
                input_file='output/phase3_output.json',
                output_file=f'output/phase4_{current_num}.json',
                max_businesses=Config.MAX_BUSINESSES_TO_EXTRACT,
                use_profile=Config.USE_CHROME_PROFILE,
                user_data_dir=Config.USER_DATA_DIR,
                profile_name=Config.PROFILE_NAME
            )
            
            self.save_checkpoint(current_num, len(queries), query)
        
        # ========== فاز ۴: کرال وبسایت‌ها ==========
        if Config.WEBSITE_CRAWL_ENABLED:
            print("\n" + "=" * 60)
            print("📍 PHASE 4: Website Crawler")
            print("=" * 60)
            crawler = WebsiteCrawler()
            crawler.run()
        else:
            print("\n⚠️ Website Crawler is disabled in Config")
        
        # ========== فاز ۵: خروجی Excel ==========
        print("\n" + "=" * 60)
        print("📍 PHASE 5: Excel Exporter")
        print("=" * 60)
        export_to_excel()
        
        self.clear_checkpoint()
        
        print("\n" + "=" * 60)
        print("✅ ALL PHASES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
    
    def _show_settings(self):
        """نمایش تنظیمات فعلی"""
        print("\n📋 Current Configuration:")
        print(f"   Headless Mode: {Config.HEADLESS}")
        print(f"   Slow Motion: {Config.SLOW_MO}ms")
        print(f"   Max Scrolls: {Config.MAX_SCROLLS}")
        print(f"   Max Businesses per Query: {Config.MAX_BUSINESSES_PER_QUERY}")
        print(f"   Max Businesses to Extract: {Config.MAX_BUSINESSES_TO_EXTRACT}")
        print(f"   Max Websites to Crawl: {Config.MAX_WEBSITES_TO_CRAWL}")
        print(f"   Website Crawler Enabled: {Config.WEBSITE_CRAWL_ENABLED}")
        print(f"   Extract Emails: {Config.EXTRACT_EMAILS}")
        print(f"   Extract Social: {Config.EXTRACT_SOCIAL}")
        print(f"   Checkpoint File: {Config.CHECKPOINT_FILE}")
        print("=" * 60)

def main():
    orchestrator = Orchestrator()
    orchestrator.run()

if __name__ == "__main__":
    main()

        # ========== فاز ۶: ارسال به سرور مرکزی ==========
        print("\n" + "=" * 60)
        print("📍 PHASE 6: Sync to Server")
        print("=" * 60)
        from app.api_sync import sync_completed_businesses
        sync_result = sync_completed_businesses(limit=500)
        print(f"✅ Synced: {sync_result['synced']} | Failed: {sync_result['failed']}")

