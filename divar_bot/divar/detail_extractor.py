"""Divar detail extraction with guarded phone reveal flow.

This module extracts structured data from a single Divar advertisement page. It
keeps all page-level heuristics isolated from runtime orchestration, queueing,
logging, and persistence.

Important design notes:
- DOM selectors are intentionally layered and conservative.
- Phone reveal is best-effort and failure-tolerant.
- The extractor returns structured status instead of throwing for normal page
  variations such as missing phone, unavailable contact button, or restricted
  pages.
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DivarDetailExtractorSettings:
    """Settings for single ad detail extraction."""

    navigation_timeout_ms: int = 45000
    after_load_pause_seconds: float = 1.0
    after_click_pause_seconds: float = 1.5
    phone_reveal_enabled: bool = True


@dataclass(frozen=True)
class DivarAdDetail:
    """Structured detail payload for one Divar advertisement."""

    source_url: str
    title: str = ""
    price_text: str = ""
    description: str = ""
    seller_name: str = ""
    phone: str = ""
    city: str = ""
    district: str = ""
    published_at_text: str = ""
    contact_status: str = "not_attempted"
    extraction_status: str = "partial"
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable detail data."""

        return asdict(self)


class DivarDetailExtractor:
    """Extracts one Divar ad detail page."""

    PHONE_RE = re.compile(r"(?:\+98|0)?9\d{9}|0\d{2,3}[-\s]?\d{7,8}")

    TITLE_SELECTORS = ["h1", "[data-testid='post-title']"]
    DESCRIPTION_SELECTORS = ["[data-testid='post-description']", "article", "main"]
    CONTACT_BUTTON_TEXTS = ["اطلاعات تماس", "نمایش شماره", "تماس", "شماره"]

    def __init__(self, settings: Optional[DivarDetailExtractorSettings] = None) -> None:
        self.settings = settings or DivarDetailExtractorSettings()

    def extract(self, page: Any, ad_url: str) -> DivarAdDetail:
        """Navigate to a Divar ad URL and extract structured data."""

        errors: List[str] = []
        try:
            page.goto(ad_url, wait_until="domcontentloaded", timeout=self.settings.navigation_timeout_ms)
            time.sleep(max(0.0, self.settings.after_load_pause_seconds))
        except Exception as exc:
            return DivarAdDetail(
                source_url=ad_url,
                extraction_status="navigation_failed",
                contact_status="not_attempted",
                errors=[f"navigation:{type(exc).__name__}:{str(exc)[:300]}"],
            )

        body_text = self._safe_body_text(page)
        title = self._first_text(page, self.TITLE_SELECTORS) or self._safe_title(page)
        description = self._first_text(page, self.DESCRIPTION_SELECTORS) or self._compact_description(body_text)
        phone = ""
        contact_status = "not_attempted"

        if self.settings.phone_reveal_enabled:
            contact_status, phone_error = self._reveal_phone(page)
            if phone_error:
                errors.append(phone_error)
            body_text = self._safe_body_text(page)
            phones = self._extract_phones(body_text)
            phone = phones[0] if phones else ""
            if phone and contact_status in {"clicked", "not_found"}:
                contact_status = "phone_found"

        if not phone:
            phones = self._extract_phones(body_text)
            phone = phones[0] if phones else ""

        status = "ok" if title or phone else "partial"
        if errors and status == "ok":
            status = "ok_with_warnings"

        return DivarAdDetail(
            source_url=ad_url,
            title=title,
            price_text=self._extract_price(body_text),
            description=description,
            seller_name=self._extract_seller_name(body_text),
            phone=phone,
            city=self._extract_city(body_text),
            district=self._extract_district(body_text),
            published_at_text=self._extract_published_at(body_text),
            contact_status=contact_status,
            extraction_status=status,
            errors=errors,
        )

    def _reveal_phone(self, page: Any) -> tuple[str, str]:
        """Try to reveal phone number by clicking a contact button."""

        for text in self.CONTACT_BUTTON_TEXTS:
            try:
                locator = page.get_by_text(text).first
                if locator.count() <= 0:
                    continue
                locator.click(timeout=5000)
                time.sleep(max(0.0, self.settings.after_click_pause_seconds))
                return "clicked", ""
            except Exception:
                continue

        try:
            buttons = page.locator("button")
            for index in range(buttons.count()):
                button = buttons.nth(index)
                label = str(button.inner_text(timeout=1000)).strip()
                if any(term in label for term in self.CONTACT_BUTTON_TEXTS):
                    button.click(timeout=5000)
                    time.sleep(max(0.0, self.settings.after_click_pause_seconds))
                    return "clicked", ""
        except Exception as exc:
            return "failed", f"phone_reveal:{type(exc).__name__}:{str(exc)[:200]}"

        return "not_found", ""

    def _first_text(self, page: Any, selectors: List[str]) -> str:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() > 0:
                    value = str(locator.inner_text(timeout=3000)).strip()
                    if value:
                        return value
            except Exception:
                continue
        return ""

    def _safe_title(self, page: Any) -> str:
        try:
            return str(page.title()).strip()
        except Exception:
            return ""

    def _safe_body_text(self, page: Any) -> str:
        try:
            return str(page.locator("body").inner_text(timeout=5000))
        except Exception:
            return ""

    def _extract_phones(self, text: str) -> List[str]:
        phones: List[str] = []
        for raw in self.PHONE_RE.findall(text or ""):
            normalized = raw.replace(" ", "").replace("-", "")
            if normalized and normalized not in phones:
                phones.append(normalized)
        return phones

    def _extract_price(self, text: str) -> str:
        for line in (text or "").splitlines():
            clean = line.strip()
            if "تومان" in clean or clean.startswith("قیمت"):
                return clean
        return ""

    def _compact_description(self, text: str) -> str:
        lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
        return "\n".join(lines[:15])[:2500]

    def _extract_seller_name(self, text: str) -> str:
        for line in (text or "").splitlines():
            clean = line.strip()
            if clean.startswith("فروشنده") or clean.startswith("نام فروشنده"):
                return clean.replace("نام فروشنده", "").replace("فروشنده", "").strip(" :")
        return ""

    def _extract_city(self, text: str) -> str:
        known = ["تهران", "کرج", "مشهد", "اصفهان", "شیراز", "تبریز", "قم", "اهواز", "رشت", "اراک"]
        for city in known:
            if city in (text or ""):
                return city
        return ""

    def _extract_district(self, text: str) -> str:
        for line in (text or "").splitlines():
            clean = line.strip()
            if "محله" in clean or "منطقه" in clean:
                return clean
        return ""

    def _extract_published_at(self, text: str) -> str:
        for line in (text or "").splitlines():
            clean = line.strip()
            if "پیش" in clean or "امروز" in clean or "دیروز" in clean:
                return clean
        return ""
