"""Captcha and restriction detection for Divar bot.

This module detects likely restriction pages, captcha flows, temporary blocks,
or suspicious responses. It intentionally focuses on detection and operational
response instead of automated solving.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class CaptchaDetectionResult:
    """Structured detection result."""

    detected: bool
    category: str = "none"
    confidence: float = 0.0
    matched_signals: List[str] = field(default_factory=list)
    recommended_action: str = "continue"

    def to_dict(self) -> Dict[str, object]:
        return {
            "detected": self.detected,
            "category": self.category,
            "confidence": self.confidence,
            "matched_signals": self.matched_signals,
            "recommended_action": self.recommended_action,
        }


class DivarCaptchaDetector:
    """Detect captcha, rate-limit, or restriction responses."""

    CAPTCHA_KEYWORDS = [
        "captcha",
        "robot",
        "امنیتی",
        "کد امنیتی",
        "verify",
        "human verification",
        "unusual traffic",
    ]

    RESTRICTION_KEYWORDS = [
        "دسترسی محدود شده",
        "too many requests",
        "temporarily blocked",
        "403",
        "forbidden",
        "access denied",
    ]

    def detect(self, page: Any) -> CaptchaDetectionResult:
        """Inspect page content and classify restriction state."""

        signals: List[str] = []
        confidence = 0.0

        text = self._safe_text(page).lower()
        url = self._safe_url(page).lower()

        for keyword in self.CAPTCHA_KEYWORDS:
            if keyword.lower() in text or keyword.lower() in url:
                signals.append(f"captcha:{keyword}")
                confidence += 0.25

        for keyword in self.RESTRICTION_KEYWORDS:
            if keyword.lower() in text or keyword.lower() in url:
                signals.append(f"restriction:{keyword}")
                confidence += 0.2

        if self._has_captcha_input(page):
            signals.append("captcha_input")
            confidence += 0.35

        if confidence >= 0.5:
            return CaptchaDetectionResult(
                detected=True,
                category="captcha_or_restricted",
                confidence=min(1.0, confidence),
                matched_signals=signals,
                recommended_action="pause_or_rotate",
            )

        if confidence > 0:
            return CaptchaDetectionResult(
                detected=True,
                category="suspicious",
                confidence=min(1.0, confidence),
                matched_signals=signals,
                recommended_action="slow_down",
            )

        return CaptchaDetectionResult(detected=False)

    def _safe_text(self, page: Any) -> str:
        try:
            return str(page.locator("body").inner_text(timeout=5000))
        except Exception:
            return ""

    def _safe_url(self, page: Any) -> str:
        try:
            return str(page.url)
        except Exception:
            return ""

    def _has_captcha_input(self, page: Any) -> bool:
        selectors = [
            "iframe[src*='captcha']",
            "input[name*='captcha']",
            "[data-testid*='captcha']",
            "img[alt*='captcha']",
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    return True
            except Exception:
                continue

        return False
