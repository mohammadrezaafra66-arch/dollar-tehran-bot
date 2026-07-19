import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/divar_bot.log", encoding="utf-8"),
    ],
)

from app.pipeline import DivarPipeline
from app.divar_chat import DivarChatMessenger
from playwright.sync_api import sync_playwright


def login_flow(phone: str) -> None:
    with sync_playwright() as p:
        messenger = DivarChatMessenger()
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(messenger.profile_path),
            channel="msedge", headless=False,
        )
        success = messenger.login(phone, context)
        context.close()
        if success:
            print("Login موفق - دفعه بعد نیاز به login نیست")
        else:
            print("Login ناموفق - دوباره امتحان کن")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ربات دیوار افراکالا")
    parser.add_argument("--url", help="URL دسته‌بندی دیوار")
    parser.add_argument("--send-messages", action="store_true")
    parser.add_argument("--no-ai", action="store_true")
    parser.add_argument("--login", action="store_true")
    parser.add_argument("--phone", help="شماره تلفن برای login")
    args = parser.parse_args()

    if args.login:
        if not args.phone:
            print("شماره تلفن را با --phone بده")
            sys.exit(1)
        login_flow(args.phone)
        sys.exit(0)

    if not args.url:
        print("URL را با --url بده")
        sys.exit(1)

    pipeline = DivarPipeline()
    stats = pipeline.run(
        listing_url=args.url,
        send_messages=args.send_messages,
        run_ai=not args.no_ai,
    )

    print("\n" + "="*50)
    print("نتیجه اجرا:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

