# app/api_sync.py - Google Search Driver
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
                   b.city, b.province, b.result_url,
                   w.email, w.instagram, w.telegram, w.whatsapp, w.extra_phones
            FROM businesses b
            LEFT JOIN website_extractions w ON w.business_id = b.id
            WHERE b.status = "done"
              AND (b.sync_status IS NULL OR b.sync_status = "pending")
            ORDER BY b.id LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()

    if not rows:
        print("Nothing to sync")
        return {"synced": 0, "failed": 0}

    headers = {"Authorization": f"Bearer {AFRAKALA_API_KEY}", "Content-Type": "application/json"}
    synced, failed = 0, 0

    for row in rows:
        business_id = row[0]
        payload = {
            "source": "google_search",
            "name": row[1] or "", "phone": row[2] or "",
            "website": row[3] or "", "address": row[4] or "",
            "city": row[5] or "", "province": row[6] or "",
            "result_url": row[7] or "",
            "email": row[8] or "", "instagram": row[9] or "",
            "telegram": row[10] or "", "whatsapp": row[11] or "",
            "extra_phones": row[12] or ""
        }
        try:
            resp = requests.post(f"{AFRAKALA_API_URL}/leads/google-search",
                                 json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                with db._get_connection() as conn:
                    conn.execute('UPDATE businesses SET sync_status = "synced" WHERE id = ?', (business_id,))
                synced += 1
            else:
                failed += 1
        except requests.exceptions.ConnectionError:
            print("API not reachable")
            failed += 1
            break
        except Exception as e:
            print(f"Sync error: {e}")
            failed += 1

    return {"synced": synced, "failed": failed}
