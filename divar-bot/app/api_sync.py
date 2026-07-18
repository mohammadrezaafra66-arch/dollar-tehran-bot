import os
import requests
import sqlite3

AFRAKALA_API_URL = os.getenv("AFRAKALA_API_URL", "http://192.168.170.8:8000")
AFRAKALA_API_KEY = os.getenv("AFRAKALA_API_KEY", "")
DB_PATH = os.getenv("DIVAR_DB_PATH", "data/divar_leads.db")


def sync_to_server(limit: int = 100) -> dict:
    if not AFRAKALA_API_KEY:
        print("AFRAKALA_API_KEY خالی — sync رد شد")
        return {"synced": 0, "failed": 0}

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, title, seller_name, phone, city, district,
               price_text, ai_analysis, source_url
        FROM divar_leads
        WHERE sync_status = 'pending' AND extraction_status = 'ok'
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    if not rows:
        return {"synced": 0, "failed": 0}

    headers = {
        "Authorization": f"Bearer {AFRAKALA_API_KEY}",
        "Content-Type": "application/json",
    }
    synced, failed = 0, 0

    for row in rows:
        lead_id = row[0]
        try:
            resp = requests.post(
                f"{AFRAKALA_API_URL}/leads/divar",
                json={
                    "source": "divar",
                    "title": row[1],
                    "seller_name": row[2],
                    "phone": row[3],
                    "city": row[4],
                    "district": row[5],
                    "price_text": row[6],
                    "ai_analysis": row[7],
                    "source_url": row[8],
                },
                headers=headers,
                timeout=10,
            )
            if resp.status_code in (200, 201):
                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "UPDATE divar_leads SET sync_status='synced' WHERE id=?",
                    (lead_id,)
                )
                conn.commit()
                conn.close()
                synced += 1
            else:
                failed += 1
        except requests.exceptions.ConnectionError:
            print("سرور در دسترس نیست")
            failed += 1
            break
        except Exception as e:
            print(f"{e}")
            failed += 1

    return {"synced": synced, "failed": failed}
