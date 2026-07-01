# app/api_mapper.py - Google Search Driver
from typing import List, Dict, Optional
from app.database import Database
from app.output_model import BusinessRecord
import json


class ApiMapper:
    """تبدیل داده‌های دیتابیس به BusinessRecord / payload افراکالا"""

    def __init__(self):
        self.db = Database()

    def get_all_business_records(self, limit: Optional[int] = None) -> List[BusinessRecord]:
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
                    b.result_url,
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
                WHERE b.status = "done"
                ORDER BY b.id
            '''
            if limit:
                query += f' LIMIT {limit}'
            cursor.execute(query)

            records = []
            for row in cursor.fetchall():
                phone_raw     = row[2] or ""
                phone_mobile  = phone_raw if phone_raw.startswith('09') else ""
                phone_landline = phone_raw if (phone_raw.startswith('0') and not phone_raw.startswith('09')) else ""

                record = BusinessRecord(
                    business_id=row[0],
                    query_text=row[8] or "",
                    name=row[1] or "",
                    phone_mobile=phone_mobile,
                    phone_landline=phone_landline,
                    website=row[3] or "",
                    address=row[4] or "",
                    city=row[5] or "",
                    province=row[6] or "",
                    # place_id/slug/rating/reviews_count → defaults (N/A for google_search)
                    place_id=row[7] or "",   # result_url in place_id field
                    email=row[9] or "",
                    instagram=row[10] or "",
                    telegram=row[11] or "",
                    whatsapp=row[12] or "",
                    extra_phones=row[13] or "",
                    extraction_date=row[14] or "",
                )
                records.append(record)

            return records

    def to_afrakala_batch_payload(self, records: List[BusinessRecord]) -> Dict:
        return {
            "total": len(records),
            "source": "google_search",
            "export_date": __import__('datetime').datetime.now().isoformat(),
            "businesses": [r.to_afrakala_payload() for r in records]
        }

    def get_stats(self) -> Dict:
        records = self.get_all_business_records()
        return {
            "total":          len(records),
            "high_quality":   sum(1 for r in records if r.quality_score == 'high'),
            "medium_quality": sum(1 for r in records if r.quality_score == 'medium'),
            "low_quality":    sum(1 for r in records if r.quality_score == 'low'),
            "has_email":      sum(1 for r in records if r.email),
            "has_social":     sum(1 for r in records if r.instagram or r.telegram or r.whatsapp),
            "has_phone":      sum(1 for r in records if r.phone_landline or r.phone_mobile),
        }

    def close(self):
        self.db.close()


if __name__ == "__main__":
    mapper = ApiMapper()
    stats = mapper.get_stats()
    print("=" * 60)
    print("📊 Data Quality Report")
    print("=" * 60)
    for k, v in stats.items():
        print(f"   {k}: {v}")
    mapper.close()
