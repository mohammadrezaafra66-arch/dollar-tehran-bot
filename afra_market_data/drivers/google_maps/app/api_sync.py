# api_sync.py - اتصال صحیح به FastAPI سرور افراکالا
import os
import requests
from app.database import Database

AFRAKALA_API_URL = os.getenv("AFRAKALA_API_URL", "http://192.168.170.8:8000")
AFRAKALA_API_KEY = os.getenv("AFRAKALA_API_KEY", "")


def sync_completed_businesses(limit: int = 100) -> dict:
    db = Database()

    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.id, b.name, b.phone, b.website, b.address,
                   b.city, b.province, b.rating, b.reviews_count, b.place_id,
                   w.email, w.instagram, w.telegram, w.whatsapp, w.extra_phones
            FROM businesses b
            LEFT JOIN website_extractions w ON w.business_id = b.id
            WHERE b.status = "done"
              AND (b.sync_status IS NULL OR b.sync_status = "pending")
            ORDER BY b.id
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()

    if not rows:
        print("✅ Nothing to sync")
        return {"synced": 0, "failed": 0}

    headers = {
        "Authorization": f"Bearer {AFRAKALA_API_KEY}",
        "Content-Type": "application/json"
    }

    synced, failed = 0, 0

    for row in rows:
        business_id = row[0]
        payload = {
            "source": "google_maps",
            "name": row[1] or "",
            "phone": row[2] or "",
            "website": row[3] or "",
            "address": row[4] or "",
            "city": row[5] or "",
            "province": row[6] or "",
            "rating": row[7],
            "reviews_count": row[8],
            "place_id": row[9] or "",
            "email": row[10] or "",
            "instagram": row[11] or "",
            "telegram": row[12] or "",
            "whatsapp": row[13] or "",
            "extra_phones": row[14] or ""
        }

        try:
            resp = requests.post(
                f"{AFRAKALA_API_URL}/leads/google-maps",
                json=payload,
                headers=headers,
                timeout=10
            )
            if resp.status_code in (200, 201):
                with db._get_connection() as conn:
                    conn.execute(
                        'UPDATE businesses SET sync_status = "synced" WHERE id = ?',
                        (business_id,)
                    )
                synced += 1
            else:
                failed += 1
                print(f"⚠️ Sync failed for id={business_id}: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            print("⚠️ API server not reachable. Will retry later.")
            failed += 1
            break
        except Exception as e:
            print(f"⚠️ Sync error: {e}")
            failed += 1

    return {"synced": synced, "failed": failed}
