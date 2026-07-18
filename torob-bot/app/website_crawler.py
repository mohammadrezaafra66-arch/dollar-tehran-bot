import re
from typing import Any

import httpx

from app.config import cfg


class WebsiteCrawler:
    def __init__(self) -> None:
        self.timeout = cfg.SELLER_CRAWL_TIMEOUT

    async def crawl(self, seller_url: str) -> dict[str, Any]:
        if not seller_url or "torob.com" in seller_url:
            return self._empty_result("skip")

        urls = [seller_url, f"{seller_url}/contact", f"{seller_url}/contact-us", f"{seller_url}/about", f"{seller_url}/تماس-با-ما"]
        result = self._empty_result("ok")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for url in urls:
                try:
                    response = await client.get(url, follow_redirects=True)
                    if response.status_code < 400:
                        text = response.text
                        result["phone"] = result["phone"] or self._extract_phone(text)
                        result["email"] = result["email"] or self._extract_email(text)
                        result["instagram"] = result["instagram"] or self._extract_instagram(text)
                        result["telegram"] = result["telegram"] or self._extract_telegram(text)
                        result["whatsapp"] = result["whatsapp"] or self._extract_whatsapp(text)
                except Exception:
                    continue

        return result

    def _empty_result(self, status: str) -> dict[str, Any]:
        return {
            "phone": None,
            "email": None,
            "instagram": None,
            "telegram": None,
            "whatsapp": None,
            "crawl_status": status,
        }

    def _extract_phone(self, text: str) -> str | None:
        match = re.search(r"09\d{9}", text)
        return match.group(0) if match else None

    def _extract_email(self, text: str) -> str | None:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return match.group(0) if match else None

    def _extract_instagram(self, text: str) -> str | None:
        match = re.search(r"https?://(?:www\.)?instagram\.com/[^\s\"']+", text, re.I)
        return match.group(0) if match else None

    def _extract_telegram(self, text: str) -> str | None:
        match = re.search(r"https?://t\.me/[^\s\"']+", text, re.I)
        return match.group(0) if match else None

    def _extract_whatsapp(self, text: str) -> str | None:
        match = re.search(r"https?://wa\.me/[^\s\"']+", text, re.I)
        return match.group(0) if match else None
