"""Category-aware crawl strategy for Divar bot.

Different Divar categories and cities should not be crawled with identical
limits. This module maps listing URLs to conservative crawl policies so the bot
can tune max ads, scroll depth, and timing profile per category.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict
from urllib.parse import urlparse


@dataclass(frozen=True)
class DivarCategoryPolicy:
    """Crawl policy for one listing category."""

    category_key: str
    max_ads: int
    max_scrolls: int
    timing_profile: str
    phone_reveal_enabled: bool = True
    priority: int = 5


class DivarCategoryStrategy:
    """Resolves listing URLs into category-specific crawl policies."""

    DEFAULT_POLICIES: Dict[str, DivarCategoryPolicy] = {
        "home-appliance": DivarCategoryPolicy(
            category_key="home-appliance",
            max_ads=150,
            max_scrolls=12,
            timing_profile="safe",
            priority=4,
        ),
        "furniture": DivarCategoryPolicy(
            category_key="furniture",
            max_ads=120,
            max_scrolls=10,
            timing_profile="normal",
            priority=5,
        ),
        "electronic-devices": DivarCategoryPolicy(
            category_key="electronic-devices",
            max_ads=100,
            max_scrolls=9,
            timing_profile="safe",
            priority=4,
        ),
        "default": DivarCategoryPolicy(
            category_key="default",
            max_ads=80,
            max_scrolls=8,
            timing_profile="safe",
            priority=6,
        ),
    }

    def __init__(self, policies: Dict[str, DivarCategoryPolicy] | None = None) -> None:
        self.policies = policies or self.DEFAULT_POLICIES

    def resolve(self, listing_url: str) -> DivarCategoryPolicy:
        """Resolve URL path into a crawl policy."""

        path = urlparse(listing_url).path.lower()
        for key, policy in self.policies.items():
            if key != "default" and key in path:
                return self._apply_env_limits(policy)
        return self._apply_env_limits(self.policies["default"])

    def _apply_env_limits(self, policy: DivarCategoryPolicy) -> DivarCategoryPolicy:
        """Apply global safety caps from environment variables."""

        max_ads_cap = int(os.getenv("DIVAR_MAX_ADS_CAP", str(policy.max_ads)))
        max_scrolls_cap = int(os.getenv("DIVAR_MAX_SCROLLS_CAP", str(policy.max_scrolls)))
        return DivarCategoryPolicy(
            category_key=policy.category_key,
            max_ads=min(policy.max_ads, max_ads_cap),
            max_scrolls=min(policy.max_scrolls, max_scrolls_cap),
            timing_profile=os.getenv("DIVAR_FORCE_TIMING_PROFILE", policy.timing_profile),
            phone_reveal_enabled=policy.phone_reveal_enabled,
            priority=policy.priority,
        )
