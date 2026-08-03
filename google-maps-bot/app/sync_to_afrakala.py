# app/sync_to_afrakala.py - نسخه اصلاح شده
import json
import os
import time
import requests
from typing import Dict, List, Optional
from app.database import Database
from app.output_model import BusinessRecord
from app.config import Config

class SimpleSync:
    """Sync ساده برای افراکالا - فقط MVP"""

    BASE_URL = os.getenv("AFRAKALA_API_URL", "http://127.0.0.1:3000").rstrip("/")
    TABLE_SLUG = os.getenv("AFRAKALA_TABLE_SLUG", "google-maps-extracted-businesses")
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.db = Database()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def sync_pending(self, limit: int = 100):
        """فقط رکوردهای pending را sync کن"""
        print("=" * 60)
        print("🔄 Syncing pending businesses to AfraKala")
        print("=" * 60)
        
        # گرفتن pending businessها
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    b.id, b.name, b.phone, b.website, b.address,
                    b.city, b.province, b.rating, b.reviews_count,
                    b.place_id, b.extracted_at,
                    w.email, w.instagram, w.telegram, w.whatsapp, w.extra_phones
                FROM businesses b
                LEFT JOIN website_extractions w ON w.business_id = b.id
                WHERE b.status = 'done' AND (b.sync_status IS NULL OR b.sync_status = 'pending')
                ORDER BY b.id
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
        
        if not rows:
            print("✅ No pending businesses to sync")
            return
        
        print(f"📋 Found {len(rows)} pending businesses")
        
        success_count = 0
        fail_count = 0
        
        for row in rows:
            business_id = row[0]
            
            # ساخت record با query_text خالی (اجباری نیست برای sync)
            record = BusinessRecord(
                business_id=business_id,
                query_text="",  # اضافه شد
                name=row[1] or "",
                phone_landline=row[2] or "",
                phone_mobile="",
                website=row[3] or "",
                address=row[4] or "",
                city=row[5] or "",
                province=row[6] or "",
                rating=row[7],
                reviews_count=row[8],
                place_id=row[9] or "",
                extraction_date=row[10] or "",
                email=row[11] or "",
                instagram=row[12] or "",
                telegram=row[13] or "",
                whatsapp=row[14] or "",
                extra_phones=row[15] or ""
            )
            
            # validation ساده
            if not record.name:
                self._mark_failed(business_id, "name is required")
                fail_count += 1
                print(f"  ❌ {business_id}: name is required")
                continue
            
            # ارسال با retry (۳ بار)
            success = self._send_with_retry(record)
            
            if success:
                self._mark_synced(business_id)
                success_count += 1
                print(f"  ✅ {record.name[:40]}... synced")
            else:
                self._mark_failed(business_id, "API error after 3 retries")
                fail_count += 1
                print(f"  ❌ {record.name[:40]}... failed")
            
            time.sleep(0.5)  # rate limit protection
        
        print(f"\n📊 Results: {success_count} synced, {fail_count} failed")
    
    def _send_with_retry(self, record: BusinessRecord, max_retries: int = 3) -> bool:
        """ارسال با retry"""
        payload = self._build_payload(record)
        
        for attempt in range(max_retries):
            try:
                response = self._post_to_api(payload)
                if response.get("success"):
                    return True
                else:
                    print(f"    Attempt {attempt + 1} failed: {response.get('error')}")
                    time.sleep(2 ** attempt)  # exponential backoff
            except Exception as e:
                print(f"    Attempt {attempt + 1} error: {e}")
                time.sleep(2 ** attempt)
        
        return False
    
    def _build_payload(self, record: BusinessRecord) -> Dict:
        """ساخت payload ساده"""
        # unique key با place_id یا ترکیب name+phone
        unique_key = record.place_id if record.place_id else f"{record.name}_{record.phone_landline}"
        
        return {
            "unique_by": ["place_id"] if record.place_id else ["name", "phone"],
            "values": {
                "name": record.name,
                "phone": record.phone_landline,
                "mobile_phone": record.phone_mobile,
                "website": record.website,
                "address": record.address,
                "province": record.province,
                "city": record.city,
                "rating": record.rating,
                "reviews_count": record.reviews_count,
                "place_id": record.place_id,
                "extracted_at": record.extraction_date,
                "meta_quality": record.quality_score,
                "email": record.email,
                "instagram": record.instagram,
                "telegram": record.telegram,
                "whatsapp": record.whatsapp,
                "extra_phones": record.extra_phones
            }
        }
    
    def _post_to_api(self, payload: Dict) -> Dict:
        """POST به API"""
        url = f"{self.BASE_URL}/api/public/bot/dynamic-tables/by-slug/{self.TABLE_SLUG}/rows/upsert"
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:100]}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _mark_synced(self, business_id: int):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE businesses 
                SET sync_status = 'synced', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (business_id,))
    
    def _mark_failed(self, business_id: int, error: str):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE businesses 
                SET sync_status = 'failed', last_error = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (error[:200], business_id))
    
    def close(self):
        self.db.close()


def main():
    print("=" * 60)
    print("🤖 Simple Sync to AfraKala")
    print("=" * 60)

    api_key = os.getenv("AFRAKALA_API_KEY", "").strip()
    if not api_key:
        api_key = input("Enter your AfraKala API Key: ").strip()
    if not api_key:
        print("❌ API Key required")
        return

    syncer = SimpleSync(api_key)
    
    print("\nOptions:")
    print("  1. Dry run (show pending count)")
    print("  2. Sync pending businesses")
    
    choice = input("\nChoose (1/2): ").strip()
    
    if choice == "1":
        with syncer.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM businesses WHERE sync_status IS NULL OR sync_status = 'pending'")
            count = cursor.fetchone()[0]
            print(f"📋 Pending businesses: {count}")
    elif choice == "2":
        confirm = input(f"⚠️ This will send data to AfraKala. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            syncer.sync_pending()
        else:
            print("❌ Cancelled")
    else:
        print("❌ Invalid choice")
    
    syncer.close()


if __name__ == "__main__":
    main()