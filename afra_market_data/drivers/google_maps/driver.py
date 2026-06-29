# driver.py - رابط استاندارد برای اتصال به پلتفرم مرکزی
import argparse
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

from app.main_orchestrator import Orchestrator
from app.api_sync import sync_completed_businesses
from app.database import Database
from app.config import Config


def run_scraper(payload: dict = None) -> dict:
    start_time = datetime.now()
    try:
        orchestrator = Orchestrator()
        orchestrator.run()
        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        return {
            "success": True,
            "summary": f"اجرا موفق در {duration} ثانیه",
            "started_at": start_time.isoformat(),
            "finished_at": end_time.isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "started_at": start_time.isoformat(),
        }


def run_sync() -> dict:
    return sync_completed_businesses(limit=200)


def get_status() -> dict:
    db = Database()
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE status = 'done'")
        done = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE status = 'pending'")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE status = 'failed'")
        failed = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM businesses WHERE sync_status = 'synced'")
        synced = cursor.fetchone()[0]

    return {
        "done": done,
        "pending": pending,
        "failed": failed,
        "synced_to_server": synced,
        "has_checkpoint": os.path.exists(Config.CHECKPOINT_FILE),
        "database_path": Config.DATABASE_PATH,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Maps Driver")
    parser.add_argument(
        "--mode",
        choices=["run", "sync", "status"],
        default="run",
        help="حالت اجرا: run=اجرای ربات, sync=ارسال به سرور, status=وضعیت"
    )
    args = parser.parse_args()

    if args.mode == "run":
        result = run_scraper()
    elif args.mode == "sync":
        result = run_sync()
    elif args.mode == "status":
        result = get_status()

    print(json.dumps(result, ensure_ascii=False, indent=2))
