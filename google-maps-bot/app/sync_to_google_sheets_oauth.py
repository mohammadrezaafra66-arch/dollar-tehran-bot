# app/sync_to_google_sheets_oauth.py
import gspread
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app.database import Database
from app.config import Config

class GoogleSheetsOAuthSync:
    """همگام‌سازی داده‌ها با Google Sheets (OAuth - فقط یک بار لاگین)"""
    
    # 👇 این را با لینک شیت خودت جایگزین کن
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1dhnXkQiuKtFjAOFb8SBupRAJdte2YyYMuln1vejbcfE/edit?gid=0#gid=0"
    
    # پیکربندی OAuth (بدون نیاز به Cloud Console)
    CLIENT_CONFIG = {
        "installed": {
            "client_id": "32555940559.apps.googleusercontent.com",
            "client_secret": "ZmssLNjJyU8sOblx6brC3rQD",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
        }
    }
    
    SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
    
    def __init__(self):
        self.db = Database()
        self.client = self._get_client()
        self.sheet = self._get_sheet()
        self._row_cache = None
    
    def _get_client(self):
        """دریافت کلاینت Google Sheets با OAuth (لاگین یک بار)"""
        creds = None
        creds_file = 'config/google_oauth_token.json'
        
        # بارگذاری token ذخیره شده قبلی
        if os.path.exists(creds_file):
            try:
                with open(creds_file, 'r') as f:
                    creds_data = json.load(f)
                creds = Credentials.from_authorized_user_info(creds_data, self.SCOPE)
            except Exception as e:
                print(f"⚠️ Error loading token: {e}")
        
        # اگر token معتبر نیست، لاگین بگیر
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("✅ Token refreshed")
                except Exception as e:
                    print(f"⚠️ Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                print("\n" + "=" * 60)
                print("🔐 Google Login Required")
                print("=" * 60)
                print("A browser window will open. Please login to your Google account")
                print("and allow access to Google Sheets.\n")
                
                flow = InstalledAppFlow.from_client_config(self.CLIENT_CONFIG, self.SCOPE)
                creds = flow.run_local_server(port=0)
                
                # ذخیره token برای دفعات بعد
                os.makedirs('config', exist_ok=True)
                with open(creds_file, 'w') as f:
                    creds_data = {
                        'token': creds.token,
                        'refresh_token': creds.refresh_token,
                        'token_uri': creds.token_uri,
                        'client_id': creds.client_id,
                        'client_secret': creds.client_secret,
                        'scopes': creds.scopes
                    }
                    json.dump(creds_data, f)
                print("✅ Credentials saved. You won't need to login again.")
        
        return gspread.authorize(creds)
    
    def _get_sheet(self):
        """دریافت شیت"""
        try:
            sheet = self.client.open_by_url(self.SHEET_URL).sheet1
        except Exception as e:
            print(f"❌ Cannot open sheet: {e}")
            print("\n💡 Make sure:")
            print("   1. The SHEET_URL is correct")
            print("   2. You have shared the sheet with your Google account")
            raise
        
        # اضافه کردن هدرها اگر شیت خالی است
        if not sheet.get_all_values():
            headers = [
                'lookup_key', 'place_id', 'name', 'phone', 'website', 'address',
                'rating', 'reviews_count', 'email', 'instagram', 'telegram',
                'meta_quality', 'sync_status', 'extracted_at', 'last_seen_at'
            ]
            sheet.append_row(headers)
            print("✅ Headers added to sheet")
        
        return sheet
    
    def _build_row_cache(self):
        """ساخت کش lookup_key → row number"""
        if self._row_cache is not None:
            return self._row_cache
        
        self._row_cache = {}
        all_data = self.sheet.get_all_values()
        
        for i, row in enumerate(all_data[1:], start=2):
            if row and len(row) > 0 and row[0]:
                self._row_cache[row[0]] = i
        
        return self._row_cache
    
    def _generate_lookup_key(self, place_id: str, name: str, phone: str, website: str) -> str:
        if place_id:
            return place_id
        return f"{name}_{phone}_{website}".replace(" ", "_")[:100]
    
    def _calculate_quality(self, phone: str, website: str, email: str) -> str:
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
    
    def sync_pending(self, batch_size: int = 50):
        """همگام‌سازی بیزینس‌های pending"""
        print("=" * 60)
        print("🔄 Syncing to Google Sheets (OAuth)")
        print("=" * 60)
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    b.id, b.place_id, b.name, b.phone, b.website, b.address,
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
        
        row_cache = self._build_row_cache()
        rows_to_append = []
        rows_to_update = []
        business_ids = []
        
        for row in rows:
            business_id = row[0]
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
            
            lookup_key = self._generate_lookup_key(place_id, name, phone, website)
            meta_quality = self._calculate_quality(phone, website, email)
            
            row_data = [
                lookup_key, place_id, name, phone, website, address,
                rating, reviews_count, email, instagram, telegram,
                meta_quality, 'synced', extracted_at, last_seen_at
            ]
            
            existing_row = row_cache.get(lookup_key)
            if existing_row:
                rows_to_update.append((existing_row, row_data))
            else:
                rows_to_append.append(row_data)
                row_cache[lookup_key] = None
            
            business_ids.append(business_id)
        
        # اضافه کردن ردیف‌های جدید به صورت batch
        if rows_to_append:
            self.sheet.append_rows(rows_to_append)
            print(f"  ✅ Added {len(rows_to_append)} new rows")
        
        # به‌روزرسانی ردیف‌های موجود
        if rows_to_update:
            for row_num, row_data in rows_to_update:
                self.sheet.update(f"A{row_num}:O{row_num}", [row_data])
            print(f"  🔄 Updated {len(rows_to_update)} rows")
        
        # علامت‌گذاری در دیتابیس
        if business_ids:
            self._mark_synced(business_ids)
        
        print(f"\n✅ Synced {len(rows)} businesses to Google Sheets")
    
    def _mark_synced(self, business_ids: list):
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
            print(f"  📝 Marked {cursor.rowcount} businesses as synced")
    
    def get_pending_count(self) -> int:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM businesses WHERE sync_status IS NULL OR sync_status = 'pending'")
            return cursor.fetchone()[0]
    
    def close(self):
        self.db.close()


def main():
    print("\n" + "=" * 60)
    print("📊 Google Sheets Sync Tool")
    print("=" * 60)
    
    syncer = GoogleSheetsOAuthSync()
    
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