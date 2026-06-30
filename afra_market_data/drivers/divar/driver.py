import argparse
import json
import sqlite3
import os

DB_PATH = os.getenv("DIVAR_DB_PATH", "data/divar_leads.db")


def get_status() -> dict:
    try:
        conn = sqlite3.connect(DB_PATH)
        total = conn.execute("SELECT COUNT(*) FROM divar_leads").fetchone()[0]
        sent = conn.execute(
            "SELECT COUNT(*) FROM divar_leads WHERE message_sent=1"
        ).fetchone()[0]
        ai_done = conn.execute(
            "SELECT COUNT(*) FROM divar_leads WHERE ai_analyzed=1"
        ).fetchone()[0]
        conn.close()
        return {"total_leads": total, "messages_sent": sent, "ai_analyzed": ai_done}
    except Exception:
        return {"total_leads": 0, "messages_sent": 0, "ai_analyzed": 0}


def run_scrape(url: str, send_messages: bool = False) -> dict:
    import sys
    sys.path.insert(0, ".")
    from pipeline import DivarPipeline
    pipeline = DivarPipeline()
    return pipeline.run(listing_url=url, send_messages=send_messages)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["run", "status", "login"], default="status")
    parser.add_argument("--url", default="")
    parser.add_argument("--send-messages", action="store_true")
    parser.add_argument("--phone", default="")
    args = parser.parse_args()

    if args.mode == "status":
        result = get_status()
    elif args.mode == "run":
        result = run_scrape(args.url, args.send_messages)
    elif args.mode == "login":
        from run import login_flow
        login_flow(args.phone)
        result = {"status": "login_done"}
    else:
        result = {}

    print(json.dumps(result, ensure_ascii=False, indent=2))
