# app/sync_to_google_sheets.py
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from app.database import Database
from app.config import Config

class GoogleSheetsSync:
    """همگام‌سازی داده‌ها با Google Sheets"""
    
    SHEET_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
    
    def __init__(self):
        self.db = Database()
        self.client = self._get_client()
        self.sheet = self._get_sheet()
        self._row_cache = None  # کش برای lookup_key → row number
    
    def _get_client(self):
        """دریافت کلاینت Google Sheets"""
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        creds_path = getattr(Config, 'GOOGLE_SHEETS_CREDENTIALS', 'config/google_sheets_credentials.json')
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        return gspread.authorize(creds)
    
    def _get_sheet(self):
        """دریافت یا ایجاد شیت"""
        try:
            sheet = self.client.open_by_url(self.SHEET_URL).sheet1
        except gspread.SpreadsheetNotFound:
            # فقط اگر Sheet واقعاً پیدا نشد، ایجاد کن
            print("📝 Sheet not found, creating new one...")
            sheet = self.client.create("Google Maps Scraper Data")
            sheet = sheet.sheet1
        except Exception as e:
            print(f"❌ Error opening sheet: {e}")
            raise
        
        # اضافه کردن هدرها اگر خالی است
        if not sheet.get_all_values():
            headers = [
                'lookup_key', 'place_id', 'name', 'phone', 'website', 'address',
                'rating', 'reviews_count', 'email', 'instagram', 'telegram',
                'meta_quality', 'sync_status', 'extracted_at', 'last_seen_at'
            ]
            sheet.append_row(headers)
        
        return sheet
    
    def _build_row_cache(self):
        """ساخت کش lookup_key → row number (یک بار در ابتدا)"""
        if self._row_cache is not None:
            return self._row_cache
        
        self._row_cache = {}
        all_data = self.sheet.get_all_values()
        
        for i, row in enumerate(all_data[1:], start=2):  # skip header
            if row and len(row) > 0:
                lookup_key = row[0]  # ستون اول lookup_key است
                if lookup_key:
                    self._row_cache[lookup_key] = i
        
        return self._row_cache
    
    def _generate_lookup_key(self, place_id: str, name: str, phone: str, website: str) -> str:
        """تولید کلید یکتا برای lookup"""
        if place_id:
            return place_id
        # fallback: ترکیب name_phone_website
        return f"{name}_{phone}_{website}".replace(" ", "_")[:100]
    
    def _calculate_quality(self, phone: str, website: str, email: str) -> str:
        """محاسبه کیفیت داده"""
        score = 0
        if phone:
            score += 1
        if website:
            score += 1
        if email:
            score += 2
        
        if score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        return "low"
    
    def _prepare_rows_data(self, rows) -> tuple:
        """آماده‌سازی داده‌ها برای ارسال به Google Sheets"""
        # ساخت کش
        row_cache = self._build_row_cache()
        
        rows_to_append = []      # ردیف‌های جدید
        rows_to_update = []      # (row_number, row_data)
        business_ids_to_sync = []  # برای آپدیت sync_status
        
        for row in rows:
            business_id = row[0]      # id داخلی
            place_id = row[1] or ""
            name = row[2] or ""
            phone = row[3] or ""
            website = row[4] or ""
            address = row[5] or ""
            rating = row[6] or ""
            reviews_count = row[7] or ""
            extracted_at = row[8] or ""
            last_seen_at = row[9] or ""
            email = row[10] or ""
            instagram = row[11] or ""
            telegram = row[12] or ""
            
            # تولید lookup_key (place_id یا fallback)
            lookup_key = self._generate_lookup_key(place_id, name, phone, website)
            meta_quality = self._calculate_quality(phone, website, email)
            
            row_data = [
                lookup_key, place_id, name, phone, website, address,
                rating, reviews_count, email, instagram, telegram,
                meta_quality, 'synced', extracted_at, last_seen_at
            ]
            
            # بررسی وجود lookup_key در کش
            existing_row = row_cache.get(lookup_key)
            
            if existing_row:
                rows_to_update.append((existing_row, row_data))
            else:
                rows_to_append.append(row_data)
                # ذخیره در کش برای بقیه batch
                row_cache[lookup_key] = None  # placeholder
            
            business_ids_to_sync.append(business_id)
        
        return rows_to_append, rows_to_update, business_ids_to_sync
    
    def sync_pending(self, batch_size: int = 50):
        """همگام‌سازی بیزینس‌های pending با Google Sheets"""
        print("=" * 60)
        print("🔄 Syncing to Google Sheets")
        print("=" * 60)
        
        # گرفتن pending businessها با id داخلی
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    b.id,
                    b.place_id, b.name, b.phone, b.website, b.address,
                    b.rating, b.reviews_count, b.extracted_at, b.last_seen_at,
                    w.email, w.instagram, w.telegram
                FROM businesses b
                LEFT JOIN website_extractions w ON w.business_id = b.id
                WHERE b.status = 'done' AND (b.sync_status IS NULL OR b.sync_status = 'pending')
                ORDER BY b.id
                LIMIT ?
            ''', (batch_size,))
            rows = cursor.fetchall()
        
        if not rows:
            print("✅ No pending businesses to sync")
            return
        
        print(f"📋 Found {len(rows)} pending businesses")
        
        # آماده‌سازی داده‌ها
        rows_to_append, rows_to_update, business_ids_to_sync = self._prepare_rows_data(rows)
        
        # اضافه کردن ردیف‌های جدید به صورت batch
        if rows_to_append:
            self.sheet.append_rows(rows_to_append)
            print(f"  ✅ Added {len(rows_to_append)} new rows")
        
        # به‌روزرسانی ردیف‌های موجود (batch update)
        if rows_to_update:
            # برای بهینه‌تر شدن، می‌توانیم batch update کنیم
            for row_num, row_data in rows_to_update:
                self.sheet.update(f"A{row_num}:O{row_num}", [row_data])
            print(f"  🔄 Updated {len(rows_to_update)} existing rows")
        
        # آپدیت sync_status در دیتابیس با id داخلی
        if business_ids_to_sync:
            self._mark_synced(business_ids_to_sync)
        
        print(f"\n✅ Synced {len(rows)} businesses to Google Sheets")
    
    def _mark_synced(self, business_ids: list):
        """علامت‌گذاری رکوردهای همگام‌سازی شده در دیتابیس (با id داخلی)"""
        if not business_ids:
            return
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(business_ids))
            cursor.execute(f'''
                UPDATE businesses 
                SET sync_status = 'synced', updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            ''', business_ids)
            print(f"  📝 Marked {cursor.rowcount} businesses as synced in DB")
    
    def get_pending_count(self) -> int:
        """تعداد بیزینس‌های pending برای sync"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM businesses WHERE sync_status IS NULL OR sync_status = 'pending'")
            return cursor.fetchone()[0]
    
    def close(self):
        self.db.close()


def main():
    syncer = GoogleSheetsSync()
    
    print("\n📋 Options:")
    print("  1. Dry run (show pending count)")
    print("  2. Sync to Google Sheets")
    
    choice = input("\n👉 Choose (1/2): ").strip()
    
    if choice == "1":
        count = syncer.get_pending_count()
        print(f"📋 Pending businesses: {count}")
    elif choice == "2":
        confirm = input("⚠️ This will send data to Google Sheets. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            syncer.sync_pending()
        else:
            print("❌ Cancelled")
    else:
        print("❌ Invalid choice")
    
    syncer.close()


if __name__ == "__main__":
    main()