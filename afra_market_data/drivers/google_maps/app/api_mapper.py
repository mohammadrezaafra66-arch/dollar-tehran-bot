# app/api_mapper.py - لایه تبدیل بین دیتابیس و API افراکالا
from typing import List, Dict, Optional
from app.database import Database
from app.output_model import BusinessRecord
import json

class ApiMapper:
    """تبدیل داده‌های دیتابیس به فرمت API افراکالا"""
    
    def __init__(self):
        self.db = Database()
    
    def get_all_business_records(self, limit: Optional[int] = None) -> List[BusinessRecord]:
        """دریافت همه بیزینس‌ها به صورت BusinessRecord"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    b.id,
                    b.name,
                    b.phone,
                    b.website,
                    b.address,
                    b.city,
                    b.province,
                    b.rating,
                    b.reviews_count,
                    b.place_id,
                    b.slug,
                    gq.query_text,
                    w.email,
                    w.instagram,
                    w.telegram,
                    w.whatsapp,
                    w.extra_phones,
                    b.extracted_at
                FROM businesses b
                LEFT JOIN generated_queries gq ON gq.id = b.query_id
                LEFT JOIN website_extractions w ON w.business_id = b.id
                WHERE b.status = 'done'
                ORDER BY b.id
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            
            records = []
            for row in cursor.fetchall():
                # تفکیک شماره موبایل و ثابت
                phone_raw = row[2] or ""
                phone_mobile = phone_raw if phone_raw.startswith('09') else ""
                phone_landline = phone_raw if phone_raw.startswith('0') and not phone_raw.startswith('09') else ""
                
                record = BusinessRecord(
                    business_id=row[0],
                    name=row[1] or "",
                    phone_landline=phone_landline,
                    phone_mobile=phone_mobile,
                    website=row[3] or "",
                    address=row[4] or "",
                    city=row[5] or "",
                    province=row[6] or "",
                    rating=row[7],
                    reviews_count=row[8],
                    place_id=row[9] or "",
                    slug=row[10] or "",
                    query_text=row[11] or "",
                    email=row[12] or "",
                    instagram=row[13] or "",
                    telegram=row[14] or "",
                    whatsapp=row[15] or "",
                    extra_phones=row[16] or "",
                    extraction_date=row[17] or ""
                )
                records.append(record)
            
            return records
    
    def to_afrakala_batch_payload(self, records: List[BusinessRecord]) -> Dict:
        """تبدیل لیست BusinessRecord به payload دسته‌ای برای API افراکالا"""
        return {
            "total": len(records),
            "export_date": __import__('datetime').datetime.now().isoformat(),
            "businesses": [r.to_afrakala_payload() for r in records]
        }
    
    def get_stats(self) -> Dict:
        """آمار کیفیت داده‌ها"""
        records = self.get_all_business_records()
        high = sum(1 for r in records if r.quality_score == 'high')
        medium = sum(1 for r in records if r.quality_score == 'medium')
        low = sum(1 for r in records if r.quality_score == 'low')
        
        return {
            "total": len(records),
            "high_quality": high,
            "medium_quality": medium,
            "low_quality": low,
            "has_email": sum(1 for r in records if r.email),
            "has_social": sum(1 for r in records if r.instagram or r.telegram or r.whatsapp),
            "has_phone": sum(1 for r in records if r.phone_landline or r.phone_mobile)
        }
    
    def close(self):
        self.db.close()


# برای اجرای تست
if __name__ == "__main__":
    mapper = ApiMapper()
    
    # آمار کیفیت
    stats = mapper.get_stats()
    print("=" * 60)
    print("📊 Data Quality Report")
    print("=" * 60)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # نمونه payload
    records = mapper.get_all_business_records(limit=5)
    payload = mapper.to_afrakala_batch_payload(records)
    
    print("\n" + "=" * 60)
    print("📦 Sample API Payload (first 5 businesses)")
    print("=" * 60)
    print(json.dumps(payload, indent=2, ensure_ascii=False)[:2000] + "...")
    
    mapper.close()