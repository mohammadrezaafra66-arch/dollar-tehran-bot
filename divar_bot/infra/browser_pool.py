"""Browser pool and context isolation runtime for Afra Automation.

This module centralizes browser lifecycle management for Playwright-based bots.
It is designed for high-concurrency deployments where many workers run in
parallel and uncontrolled Chromium launches would cause memory exhaustion,
zombie processes, profile corruption, and unstable behavior.

Design goals:
- bounded browser/context concurrency
- context-level isolation per job
- config-driven timeouts and pool sizes
- graceful fallback when Playwright is not installed
- explicit lease/release lifecycle
- safe shutdown for Kubernetes pod termination
"""

from __future__ import annotations

import os
import socket
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, Iterator, List, Optional


class BrowserPoolUnavailable(RuntimeError):
    """Raised when the browser runtime cannot be initialized."""


@dataclass(frozen=True)
class BrowserPoolSettings:
    """Configuration for browser and context lifecycle."""

    max_browsers: int
    max_contexts_per_browser: int
    headless: bool
    launch_timeout_ms: int
    default_navigation_timeout_ms: int
    slow_mo_ms: int
    user_agent: Optional[str]
    locale: str
    timezone_id: str
    chromium_args: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "BrowserPoolSettings":
        """Build settings from environment variables."""

        args = os.getenv("AFRA_CHROMIUM_ARGS", "--disable-dev-shm-usage,--no-sandbox")
        return cls(
            max_browsers=int(os.getenv("AFRA_BROWSER_POOL_MAX_BROWSERS", "2")),
            max_contexts_per_browser=int(os.getenv("AFRA_BROWSER_POOL_MAX_CONTEXTS", "4")),
            headless=os.getenv("AFRA_BROWSER_HEADLESS", "true").lower() == "true",
            launch_timeout_ms=int(os.getenv("AFRA_BROWSER_LAUNCH_TIMEOUT_MS", "45000")),
            default_navigation_timeout_ms=int(os.getenv("AFRA_BROWSER_NAV_TIMEOUT_MS", "45000")),
            slow_mo_ms=int(os.getenv("AFRA_BROWSER_SLOW_MO_MS", "0")),
            user_agent=os.getenv("AFRA_BROWSER_USER_AGENT") or None,
            locale=os.getenv("AFRA_BROWSER_LOCALE", "fa-IR"),
            timezone_id=os.getenv("AFRA_BROWSER_TIMEZONE", "Asia/Tehran"),
            chromium_args=[item.strip() for item in args.split(",") if item.strip()],
        )


@dataclass
class BrowserLease:
    """A leased isolated browser context for one unit of work."""

    lease_id: str
    browser_id: str
    context: Any
    page: Any
    created_at: float
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class BrowserSlot:
    """Internal browser slot with active context count."""

    browser_id: str
    browser: Any
    active_contexts: int = 0
    created_at: float = field(default_factory=time.time)


class BrowserPool:
    """Bounded Playwright browser pool with isolated contexts per lease."""

    def __init__(self, settings: Optional[BrowserPoolSettings] = None) -> None:
        self.settings = settings or BrowserPoolSettings.from_env()
        self.instance_id = os.getenv("DIVAR_BOT_INSTANCE_ID", socket.gethostname())
        self._lock = Lock()
        self._playwright = None
        self._slots: List[BrowserSlot] = []
        self._leases: Dict[str, BrowserLease] = {}
        self._started = False

    def _load_playwright(self):
        """Import Playwright lazily so non-browser workers can still run."""

        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise BrowserPoolUnavailable("playwright is not installed") from exc
        return sync_playwright

    def start(self) -> None:
        """Start Playwright runtime if not already running."""

        with self._lock:
            if self._started:
                return
            sync_playwright = self._load_playwright()
            self._playwright = sync_playwright().start()
            self._started = True

    def _launch_browser(self) -> BrowserSlot:
        """Launch a browser and register it as a slot."""

        if not self._started:
            self.start()

        browser_id = f"browser-{self.instance_id}-{len(self._slots) + 1}"
        browser = self._playwright.chromium.launch(
            headless=self.settings.headless,
            slow_mo=self.settings.slow_mo_ms,
            args=self.settings.chromium_args,
            timeout=self.settings.launch_timeout_ms,
        )
        slot = BrowserSlot(browser_id=browser_id, browser=browser)
        self._slots.append(slot)
        return slot

    def _select_slot(self) -> BrowserSlot:
        """Select a slot with available context capacity or create one."""

        available = [slot for slot in self._slots if slot.active_contexts < self.settings.max_contexts_per_browser]
        if available:
            return sorted(available, key=lambda item: item.active_contexts)[0]

        if len(self._slots) < self.settings.max_browsers:
            return self._launch_browser()

        raise BrowserPoolUnavailable("browser pool capacity exhausted")

    def acquire(self, metadata: Optional[Dict[str, str]] = None) -> BrowserLease:
        """Acquire an isolated browser context and page for a job."""

        with self._lock:
            slot = self._select_slot()
            context_kwargs: Dict[str, Any] = {
                "locale": self.settings.locale,
                "timezone_id": self.settings.timezone_id,
            }
            if self.settings.user_agent:
                context_kwargs["user_agent"] = self.settings.user_agent

            context = slot.browser.new_context(**context_kwargs)
            context.set_default_navigation_timeout(self.settings.default_navigation_timeout_ms)
            page = context.new_page()
            page.set_default_timeout(self.settings.default_navigation_timeout_ms)

            slot.active_contexts += 1
            lease = BrowserLease(
                lease_id=str(uuid.uuid4()),
                browser_id=slot.browser_id,
                context=context,
                page=page,
                created_at=time.time(),
                metadata=metadata or {},
            )
            self._leases[lease.lease_id] = lease
            return lease

    def release(self, lease: BrowserLease) -> None:
        """Release a leased context and decrement slot usage."""

        with self._lock:
            if lease.lease_id not in self._leases:
                return

            try:
                lease.context.close()
            finally:
                self._leases.pop(lease.lease_id, None)
                for slot in self._slots:
                    if slot.browser_id == lease.browser_id:
                        slot.active_contexts = max(0, slot.active_contexts - 1)
                        break

    @contextmanager
    def session(self, metadata: Optional[Dict[str, str]] = None) -> Iterator[BrowserLease]:
        """Context manager that always releases the browser lease."""

        lease = self.acquire(metadata=metadata)
        try:
            yield lease
        finally:
            self.release(lease)

    def snapshot(self) -> Dict[str, Any]:
        """Return pool state for health checks and metrics."""

        with self._lock:
            return {
                "instance_id": self.instance_id,
                "started": self._started,
                "max_browsers": self.settings.max_browsers,
                "max_contexts_per_browser": self.settings.max_contexts_per_browser,
                "browser_count": len(self._slots),
                "active_leases": len(self._leases),
                "slots": [
                    {
                        "browser_id": slot.browser_id,
                        "active_contexts": slot.active_contexts,
                        "created_at": slot.created_at,
                    }
                    for slot in self._slots
                ],
            }

    def shutdown(self) -> None:
        """Close all contexts and browsers. Safe for Kubernetes preStop hooks."""

        with self._lock:
            for lease in list(self._leases.values()):
                try:
                    lease.context.close()
                except Exception:
                    pass
            self._leases.clear()

            for slot in self._slots:
                try:
                    slot.browser.close()
                except Exception:
                    pass
            self._slots.clear()

            if self._playwright is not None:
                try:
                    self._playwright.stop()
                except Exception:
                    pass

            self._playwright = None
            self._started = False
