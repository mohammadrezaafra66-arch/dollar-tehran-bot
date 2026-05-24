"""Human-like timing profiles for Divar bot.

The goal of this module is not to bypass security systems. It prevents brittle,
robotic, synchronized execution patterns by making crawler pacing configurable,
traceable, and appropriate for normal browser automation workloads.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TimingRange:
    """A bounded delay range in seconds."""

    minimum: float
    maximum: float

    def sample(self) -> float:
        """Return a random delay inside the configured range."""

        if self.maximum <= self.minimum:
            return max(0.0, self.minimum)
        return random.uniform(self.minimum, self.maximum)


@dataclass(frozen=True)
class HumanTimingProfile:
    """Timing profile used across Divar browsing actions."""

    name: str
    before_listing_open: TimingRange
    between_scrolls: TimingRange
    before_ad_open: TimingRange
    after_ad_open: TimingRange
    before_phone_click: TimingRange
    after_phone_click: TimingRange
    between_ads: TimingRange


class HumanTimingProfiles:
    """Factory for safe, config-driven timing profiles."""

    DEFAULTS: Dict[str, HumanTimingProfile] = {
        "test": HumanTimingProfile(
            name="test",
            before_listing_open=TimingRange(0.1, 0.3),
            between_scrolls=TimingRange(0.1, 0.3),
            before_ad_open=TimingRange(0.1, 0.3),
            after_ad_open=TimingRange(0.1, 0.3),
            before_phone_click=TimingRange(0.1, 0.3),
            after_phone_click=TimingRange(0.1, 0.3),
            between_ads=TimingRange(0.1, 0.3),
        ),
        "safe": HumanTimingProfile(
            name="safe",
            before_listing_open=TimingRange(3, 8),
            between_scrolls=TimingRange(4, 11),
            before_ad_open=TimingRange(6, 18),
            after_ad_open=TimingRange(4, 12),
            before_phone_click=TimingRange(8, 22),
            after_phone_click=TimingRange(4, 10),
            between_ads=TimingRange(12, 35),
        ),
        "normal": HumanTimingProfile(
            name="normal",
            before_listing_open=TimingRange(1, 4),
            between_scrolls=TimingRange(2, 6),
            before_ad_open=TimingRange(3, 10),
            after_ad_open=TimingRange(2, 7),
            before_phone_click=TimingRange(5, 14),
            after_phone_click=TimingRange(2, 7),
            between_ads=TimingRange(6, 18),
        ),
    }

    @classmethod
    def from_env(cls) -> HumanTimingProfile:
        """Load timing profile by name from environment."""

        profile_name = os.getenv("DIVAR_TIMING_PROFILE", "safe").lower().strip()
        return cls.DEFAULTS.get(profile_name, cls.DEFAULTS["safe"])


class HumanTimingController:
    """Applies sampled delays and returns values for logging/metrics."""

    def __init__(self, profile: Optional[HumanTimingProfile] = None, sleep_enabled: Optional[bool] = None) -> None:
        self.profile = profile or HumanTimingProfiles.from_env()
        self.sleep_enabled = sleep_enabled if sleep_enabled is not None else os.getenv("DIVAR_TIMING_SLEEP", "true").lower() == "true"

    def wait(self, action: str) -> float:
        """Wait for an action-specific delay and return actual delay seconds."""

        timing_range = self._range_for(action)
        delay = timing_range.sample()
        if self.sleep_enabled and delay > 0:
            time.sleep(delay)
        return delay

    def _range_for(self, action: str) -> TimingRange:
        mapping = {
            "before_listing_open": self.profile.before_listing_open,
            "between_scrolls": self.profile.between_scrolls,
            "before_ad_open": self.profile.before_ad_open,
            "after_ad_open": self.profile.after_ad_open,
            "before_phone_click": self.profile.before_phone_click,
            "after_phone_click": self.profile.after_phone_click,
            "between_ads": self.profile.between_ads,
        }
        return mapping.get(action, self.profile.between_ads)
