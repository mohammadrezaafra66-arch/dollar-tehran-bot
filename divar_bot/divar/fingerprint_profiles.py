"""Browser fingerprint profile management.

This module provides conservative browser profile presets. The goal is runtime
consistency and reduction of obviously uniform automation fingerprints, not
stealth escalation.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass(frozen=True)
class BrowserFingerprintProfile:
    """One browser fingerprint preset."""

    profile_id: str
    locale: str
    timezone: str
    viewport_width: int
    viewport_height: int
    user_agent: str
    platform: str
    color_scheme: str = "light"

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class DivarFingerprintProfiles:
    """Provides realistic, region-consistent browser profiles."""

    DEFAULT_PROFILES: List[BrowserFingerprintProfile] = [
        BrowserFingerprintProfile(
            profile_id="fa-desktop-chrome-1",
            locale="fa-IR",
            timezone="Asia/Tehran",
            viewport_width=1366,
            viewport_height=768,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            platform="Win32",
        ),
        BrowserFingerprintProfile(
            profile_id="fa-desktop-chrome-2",
            locale="fa-IR",
            timezone="Asia/Tehran",
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
            platform="Win32",
        ),
        BrowserFingerprintProfile(
            profile_id="fa-linux-chrome-1",
            locale="fa-IR",
            timezone="Asia/Tehran",
            viewport_width=1536,
            viewport_height=864,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            platform="Linux x86_64",
        ),
    ]

    @classmethod
    def random_profile(cls) -> BrowserFingerprintProfile:
        """Return a conservative randomized profile."""

        return random.choice(cls.DEFAULT_PROFILES)

    @classmethod
    def by_id(cls, profile_id: str) -> BrowserFingerprintProfile:
        """Return profile by id or fallback."""

        for profile in cls.DEFAULT_PROFILES:
            if profile.profile_id == profile_id:
                return profile
        return cls.DEFAULT_PROFILES[0]

    @classmethod
    def from_env(cls) -> BrowserFingerprintProfile:
        """Resolve profile from environment variables."""

        requested = os.getenv("DIVAR_FINGERPRINT_PROFILE", "random").strip()
        if requested == "random":
            return cls.random_profile()
        return cls.by_id(requested)
