"""رابط استاندارد ربات دیوار.

استفاده:
  python driver.py --mode status
  python driver.py --mode run --url "https://divar.ir/s/tehran/electronic"
  python driver.py --mode sync
  python driver.py --mode login --phone "09XXXXXXXXX"
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.pipeline import DivarPipeline
from app.api_sync import sync_to_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["run", "status", "sync", "login"], default="status")
    parser.add_argument("--url", default="")
    parser.add_argument("--send-messages", action="store_true")
    parser.add_argument("--phone", default="")
    args = parser.parse_args()

    if args.mode == "status":
        from app.database import get_stats
        result = get_stats()
    elif args.mode == "run":
        assert args.url, "--url لازم است"
        pipeline = DivarPipeline()
        result = pipeline.run(listing_url=args.url, send_messages=args.send_messages)
    elif args.mode == "sync":
        result = sync_to_server()
    elif args.mode == "login":
        assert args.phone, "--phone لازم است"
        from app.divar_chat import DivarChatMessenger
        from playwright.sync_api import sync_playwright
        profile_id = os.getenv("DIVAR_LOGIN_PROFILE_ID", "divar-profile-1")
        messenger = DivarChatMessenger(profile_id=profile_id)
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(messenger.profile_path),
                headless=False,
            )
            success = messenger.login(args.phone, context)
            context.close()
        result = {"login": "success" if success else "failed"}
    else:
        result = {}

    print(json.dumps(result, ensure_ascii=False, indent=2))
