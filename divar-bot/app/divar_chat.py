from __future__ import annotations

import os
import time
import random
import logging
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext

from app.personalizer import build_message
from app.send_log import log_sent, get_daily_sent_count

logger = logging.getLogger(__name__)

DIVAR_URL = "https://divar.ir"
PROFILE_DIR = os.getenv("DIVAR_PROFILE_DIR", "runtime/profiles/divar")
DAILY_LIMIT = int(os.getenv("DIVAR_DAILY_MESSAGE_LIMIT", "30"))
MIN_DELAY = float(os.getenv("DIVAR_MIN_DELAY_SECONDS", "20"))
MAX_DELAY = float(os.getenv("DIVAR_MAX_DELAY_SECONDS", "60"))


class DivarChatResult:
    def __init__(self, success: bool, status: str, error: str = ""):
        self.success = success
        self.status = status
        self.error = error


class DivarChatMessenger:

    def __init__(self, profile_id: str = "divar-profile-1") -> None:
        self.profile_id = profile_id
        self.profile_path = Path(PROFILE_DIR) / profile_id
        self.profile_path.mkdir(parents=True, exist_ok=True)

    def is_logged_in(self, page: Page) -> bool:
        try:
            page.goto(DIVAR_URL, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            login_btn = page.locator("a[href*='login'], button:has-text('ورود')").first
            return login_btn.count() == 0
        except Exception:
            return False

    def login(self, phone: str, context: BrowserContext, sample_url: str = "https://divar.ir/s/tehran") -> bool:
        page = context.new_page()
        try:
            page.goto(sample_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(3)

            first_card = page.locator("a[href*='/v/']").first
            if first_card.count() == 0:
                logger.error("هیچ آگهی پیدا نشد")
                return False
            listing_url = first_card.get_attribute("href")
            if not listing_url:
                logger.error("لینک آگهی پیدا نشد")
                return False
            if not listing_url.startswith("http"):
                listing_url = DIVAR_URL + listing_url

            page.goto(listing_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)

            contact_btn = page.locator("button:has-text('اطلاعات تماس'), button:has-text('تماس با فروشنده')").first
            if contact_btn.count() == 0:
                logger.error("دکمه اطلاعات تماس پیدا نشد")
                return False
            contact_btn.click()
            time.sleep(3)

            phone_input = page.locator("input[type='tel'], input[placeholder*='موبایل'], input[placeholder*='شماره']").first
            if phone_input.count() == 0:
                logger.error("فیلد شماره تلفن در پاپ‌آپ پیدا نشد")
                return False
            phone_input.fill(phone)
            time.sleep(1)
            submit_btn = page.locator("button[type='submit']").first
            submit_btn.click()
            time.sleep(3)
            otp_file = Path(os.getcwd()) / "data" / f"divar_otp_{self.profile_id}.txt"
            logger.info(f"Waiting for OTP in: {otp_file}")
            max_wait = 120
            waited = 0
            otp = ""
            while waited < max_wait:
                if otp_file.exists():
                    otp = otp_file.read_text(encoding="utf-8").strip()
                    if otp:
                        otp_file.unlink(missing_ok=True)
                        break
                time.sleep(2)
                waited += 2
            if not otp:
                logger.error("OTP دریافت نشد — timeout")
                return False
            otp_input = page.locator("input[type='number'], input[maxlength='6'], input[placeholder*='کد']").first
            if otp_input.count() == 0:
                logger.error("فیلد OTP پیدا نشد")
                return False
            otp_input.fill(otp)
            time.sleep(1)
            confirm_btn = page.locator("button[type='submit']").first
            confirm_btn.click()
            time.sleep(4)
            if self.is_logged_in(page):
                logger.info("Login موفق - session ذخیره شد")
                page.close()
                return True
            logger.error("Login ناموفق")
            page.close()
            return False
        except Exception as exc:
            logger.error(f"Login error: {exc}")
            return False

    def send_message(self, listing_url: str, message: str, page: Page) -> DivarChatResult:
        try:
            page.goto(listing_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(random.uniform(2, 4))
            msg_button_selectors = [
                "button:has-text('ارسال پیام')",
                "button:has-text('پیام به فروشنده')",
                "a:has-text('ارسال پیام')",
                "[data-testid*='message']",
                "button:has-text('چت')",
            ]
            msg_button = None
            for selector in msg_button_selectors:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible():
                    msg_button = btn
                    break
            if msg_button is None:
                return DivarChatResult(False, "no_message_button", "دکمه پیام پیدا نشد")
            msg_button.click()
            time.sleep(random.uniform(1.5, 3))
            text_input = page.locator(
                "textarea, input[type='text'][placeholder*='پیام'], [contenteditable='true']"
            ).first
            if text_input.count() == 0:
                return DivarChatResult(False, "no_text_input", "کادر متن پیدا نشد")
            text_input.click()
            time.sleep(0.5)
            lines = message.split("\n")
            for line_index, line in enumerate(lines):
                for char in line:
                    text_input.type(char)
                    time.sleep(random.uniform(0.04, 0.12))
                if line_index < len(lines) - 1:
                    text_input.press("Shift+Enter")
                    time.sleep(random.uniform(0.05, 0.15))
            time.sleep(random.uniform(0.5, 1.5))
            send_selectors = [
                "button:has-text('ارسال')",
                "button[type='submit']",
                "[data-testid*='send']",
            ]
            send_button = None
            for selector in send_selectors:
                btn = page.locator(selector).first
                if btn.count() > 0 and btn.is_visible():
                    send_button = btn
                    break
            if send_button is None:
                text_input.press("Enter")
            else:
                send_button.click()
            time.sleep(2)
            return DivarChatResult(True, "sent")
        except Exception as exc:
            return DivarChatResult(False, "error", str(exc)[:200])

    def run_campaign(self, leads: list, message_template: Optional[str] = None) -> dict:
        stats = {"sent": 0, "failed": 0, "skipped": 0, "limit_reached": False}
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_path),
                headless=False,
                slow_mo=random.randint(100, 300),
                locale="fa-IR",
                timezone_id="Asia/Tehran",
            )
            page = context.new_page()
            if not self.is_logged_in(page):
                logger.warning("Session منقضی شده. لطفا دوباره login کن.")
                page.close()
                context.close()
                return stats
            for lead in leads:
                daily_sent = get_daily_sent_count()
                if daily_sent >= DAILY_LIMIT:
                    logger.info(f"محدودیت روزانه ({DAILY_LIMIT}) رسیده")
                    stats["limit_reached"] = True
                    break
                if not lead.get("source_url"):
                    stats["skipped"] += 1
                    continue
                message = build_message(lead, message_template)
                result = self.send_message(lead["source_url"], message, page)
                log_sent(
                    lead_id=lead.get("id", 0),
                    listing_url=lead["source_url"],
                    phone=lead.get("phone", ""),
                    message_text=message,
                    status=result.status,
                    error_msg=result.error,
                )
                if result.success:
                    stats["sent"] += 1
                    logger.info(f"ارسال موفق: {lead.get('title','')[:40]}")
                else:
                    stats["failed"] += 1
                    logger.warning(f"ارسال ناموفق: {result.error}")
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                logger.info(f"انتظار {delay:.0f} ثانیه...")
                time.sleep(delay)
            page.close()
            context.close()
        return stats

