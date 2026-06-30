"""Divar page extraction primitives.

This module contains small, testable extraction helpers for Divar pages. It does
not own browser lifecycle, queues, retries, logging, or persistence. Those are
handled by the runtime layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DivarLead:
    """Normalized lead extracted from a Divar listing page."""

    source_url: str
    title: str = ""
    price_text: str = ""
    description: str = ""
    seller_name: str = ""
    phone: str = ""
    city: str = ""
    district: str = ""
    extracted_status: str = "partial"

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable lead data."""

        return asdict(self)


class DivarPageExtractor:
    """Extracts a conservative lead payload from a rendered Divar page."""

    PHONE_RE = re.compile(r"(?:\+98|0)?9\d{9}|0\d{2,3}[-\s]?\d{7,8}")

    def extract(self, page: Any, url: str) -> DivarLead:
        """Extract a normalized DivarLead from a Playwright-like page."""

        title = self._safe_text(page, "h1") or self._safe_title(page)
        body_text = self._safe_body_text(page)
        phones = self.extract_phones(body_text)

        return DivarLead(
            source_url=url,
            title=title,
            price_text=self._extract_price(body_text),
            description=self._extract_description(body_text),
            phone=phones[0] if phones else "",
            city=self._extract_city(body_text),
            district=self._extract_district(body_text),
            extracted_status="ok" if title or phones else "partial",
        )

    def extract_phones(self, text: str) -> List[str]:
        """Extract candidate Iranian phone numbers from text."""

        found = []
        for match in self.PHONE_RE.findall(text or ""):
            normalized = match.replace(" ", "").replace("-", "")
            if normalized not in found:
                found.append(normalized)
        return found

    def _safe_text(self, page: Any, selector: str) -> str:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                return str(locator.inner_text(timeout=3000)).strip()
        except Exception:
            return ""
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

    def _extract_price(self, text: str) -> str:
        for line in (text or "").splitlines():
            if "تومان" in line or "قیمت" in line:
                return line.strip()
        return ""

    def _extract_description(self, text: str) -> str:
        lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
        return "\n".join(lines[:12])[:2000]

    def _extract_city(self, text: str) -> str:
        known_cities = ["تهران", "کرج", "مشهد", "اصفهان", "شیراز", "تبریز", "قم", "اهواز"]
        for city in known_cities:
            if city in (text or ""):
                return city
        return ""

    def _extract_district(self, text: str) -> str:
        for line in (text or "").splitlines():
            if "محله" in line or "منطقه" in line:
                return line.strip()
        return ""
