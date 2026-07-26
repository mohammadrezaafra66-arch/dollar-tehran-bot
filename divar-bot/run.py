import argparse
import logging
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/divar_bot.log", encoding="utf-8"),
    ],
)

from app.pipeline import DivarPipeline
from playwright.sync_api import sync_playwright
import re, time
from pathlib import Path


def login_flow(phone: str, profile_id: str = "divar-profile-1") -> None:
    profile_base = os.getenv("DIVAR_PROFILE_DIR", "runtime/profiles/divar")
    # اگه DIVAR_PROFILE_DIR قبلاً شامل profile_id هست، از همون استفاده کن
    if profile_base.endswith(profile_id):
        profile_path = Path(profile_base)
    else:
        profile_path = Path(profile_base) / profile_id
    profile_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=True,
            locale="fa-IR",
            timezone_id="Asia/Tehran",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        try:
            page.goto("https://divar.ir/s/tehran", timeout=60000)
            time.sleep(5)
            links = page.locator("a[href*=\'/v/\']").all()
            if not links:
                print("آگهی پیدا نشد")
                context.close()
                return
            url = "https://divar.ir" + links[0].get_attribute("href")
            page.goto(url, timeout=60000)
            time.sleep(5)
            page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll("button"));
                    const btn = buttons.find(b =>
                        b.textContent.includes("اطلاعات تماس") &&
                        !b.className.includes("a11y"));
                    if (btn) btn.click();
                }
            """)
            time.sleep(4)
            tel = page.locator("input[type=\'tel\']").first
            if tel.count() == 0:
                print("فیلد شماره تلفن پیدا نشد")
                context.close()
                return
            tel.fill(phone)
            time.sleep(1)
            page.keyboard.press("Enter")
            time.sleep(4)
            print(f"کد OTP برای {phone}: ", flush=True)
            otp = input().strip()
            page.evaluate(f"""
                () => {{
                    const inputs = Array.from(document.querySelectorAll("input[type=\'text\']"))
                        .filter(i => !i.placeholder || !i.placeholder.includes("جستجو"));
                    const otp = "{otp}";
                    inputs.slice(0, otp.length).forEach((inp, idx) => {{
                        const setter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, "value").set;
                        setter.call(inp, otp[idx]);
                        inp.dispatchEvent(new Event("input", {{bubbles: true}}));
                    }});
                }}
            """)
            time.sleep(5)
            body = page.locator("body").inner_text(timeout=5000)
            phones = re.findall(r"(?:\+98|0)?9\d{9}", body)
            if phones:
                print(f"Login موفق — شماره: {phones[0]}")
            else:
                print("Login انجام شد — session ذخیره شد")
        except Exception as e:
            print(f"خطا: {e}")
        finally:
            context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ربات دیوار افراکالا")
    parser.add_argument("--url", help="URL دسته‌بندی دیوار")
    parser.add_argument("--send-messages", action="store_true")
    parser.add_argument("--no-ai", action="store_true")
    parser.add_argument("--login", action="store_true")
    parser.add_argument("--phone", help="شماره تلفن برای login")
    parser.add_argument("--profile", default="divar-profile-1", help="profile ID")
    args = parser.parse_args()

    if args.login:
        if not args.phone:
            print("شماره تلفن را با --phone بده")
            sys.exit(1)
        login_flow(args.phone, args.profile)
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
