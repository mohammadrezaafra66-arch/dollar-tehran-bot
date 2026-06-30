"""Divar listing crawler.

This module collects advertisement URLs from a Divar listing/search page. It is
kept separate from detail extraction so list crawling can be retried, tested,
and rate-limited independently.

The crawler is conservative: it does not assume a fixed DOM contract beyond
links containing Divar listing paths. Selectors can be improved later as real
HTML samples are collected.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, List, Set
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True)
class DivarListingCrawlerSettings:
    """Settings for Divar listing crawling."""

    max_scrolls: int = 10
    scroll_pause_seconds: float = 1.5
    max_ads: int = 200
    base_url: str = "https://divar.ir"


@dataclass(frozen=True)
class DivarAdLink:
    """A discovered Divar advertisement link."""

    url: str
    slug: str
    source_listing_url: str


@dataclass(frozen=True)
class DivarListingResult:
    """Result of crawling one listing/search URL."""

    source_url: str
    ads: List[DivarAdLink] = field(default_factory=list)
    status: str = "ok"
    error: str = ""


class DivarListingCrawler:
    """Collects Divar advertisement URLs from a listing page."""

    AD_PATH_RE = re.compile(r"/(?:v|p)/([^/?#]+)")

    def __init__(self, settings: DivarListingCrawlerSettings | None = None) -> None:
        self.settings = settings or DivarListingCrawlerSettings()

    def crawl(self, page: Any, listing_url: str) -> DivarListingResult:
        """Open a listing page, scroll it, and collect ad URLs."""

        try:
            page.goto(listing_url, wait_until="domcontentloaded")
            self._scroll(page)
            ads = self._collect_links(page, listing_url)
            return DivarListingResult(source_url=listing_url, ads=ads, status="ok")
        except Exception as exc:
            return DivarListingResult(
                source_url=listing_url,
                ads=[],
                status="failed",
                error=f"{type(exc).__name__}: {str(exc)[:300]}",
            )

    def _scroll(self, page: Any) -> None:
        """Scroll listing page to load more ads."""

        for _ in range(max(0, self.settings.max_scrolls)):
            try:
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            except Exception:
                break
            time.sleep(max(0.0, self.settings.scroll_pause_seconds))

    def _collect_links(self, page: Any, listing_url: str) -> List[DivarAdLink]:
        """Collect unique Divar ad links from anchor tags."""

        links = page.locator("a[href]")
        total = links.count()
        seen: Set[str] = set()
        ads: List[DivarAdLink] = []

        for index in range(total):
            if len(ads) >= self.settings.max_ads:
                break
            try:
                href = links.nth(index).get_attribute("href")
            except Exception:
                continue
            if not href:
                continue

            absolute_url = urljoin(self.settings.base_url, href)
            parsed = urlparse(absolute_url)
            match = self.AD_PATH_RE.search(parsed.path)
            if not match:
                continue

            slug = match.group(1)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if clean_url in seen:
                continue
            seen.add(clean_url)
            ads.append(DivarAdLink(url=clean_url, slug=slug, source_listing_url=listing_url))

        return ads
