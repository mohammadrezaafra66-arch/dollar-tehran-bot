# driver.py - Google Search Driver
import argparse, json, os, sys
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
        Orchestrator().run()
        end_time = datetime.now()
        return {"success": True, "summary": f"done in {(end_time-start_time).seconds}s",
                "started_at": start_time.isoformat(), "finished_at": end_time.isoformat()}
    except Exception as e:
        return {"success": False, "error": str(e), "started_at": start_time.isoformat()}


def run_sync() -> dict:
    return sync_completed_businesses(limit=200)


def get_status() -> dict:
    db = Database()
    stats = db.get_stats()
    stats["has_checkpoint"] = os.path.exists(Config.CHECKPOINT_FILE)
    stats["database_path"] = Config.DATABASE_PATH
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Search Driver")
    parser.add_argument("--mode", choices=["run", "sync", "status"], default="run")
    args = parser.parse_args()
    result = {"run": run_scraper, "sync": run_sync, "status": get_status}[args.mode]()
    print(json.dumps(result, ensure_ascii=False, indent=2))
