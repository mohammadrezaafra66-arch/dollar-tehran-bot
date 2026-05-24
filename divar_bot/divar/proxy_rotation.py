"""Proxy rotation and health tracking for Divar bot.

This module manages reusable proxy endpoints with lightweight health scoring.
It does not attempt anonymity escalation or stealth behavior. The goal is
operational resilience and distribution of network load.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProxyEndpoint:
    """One configured proxy endpoint."""

    proxy_id: str
    server: str
    username: str = ""
    password: str = ""
    health_score: float = 1.0
    cooldown_until: float = 0.0
    failure_count: int = 0
    success_count: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        """Return whether the proxy is available for allocation."""

        return time.time() >= self.cooldown_until and self.health_score > 0.15


class ProxyRotationManager:
    """Allocates and tracks proxy endpoint health."""

    def __init__(self, proxies: Optional[List[ProxyEndpoint]] = None) -> None:
        self.proxies = proxies or self._load_from_env()

    def allocate(self) -> Optional[ProxyEndpoint]:
        """Allocate a healthy proxy endpoint."""

        available = [proxy for proxy in self.proxies if proxy.available]
        if not available:
            return None

        weighted: List[ProxyEndpoint] = []
        for proxy in available:
            weight = max(1, int(proxy.health_score * 10))
            weighted.extend([proxy] * weight)

        return random.choice(weighted)

    def report_success(self, proxy_id: str) -> None:
        """Increase proxy health after successful usage."""

        proxy = self._find(proxy_id)
        if not proxy:
            return

        proxy.success_count += 1
        proxy.health_score = min(1.0, proxy.health_score + 0.05)

    def report_failure(self, proxy_id: str, cooldown_seconds: float = 300.0) -> None:
        """Reduce proxy health and apply cooldown."""

        proxy = self._find(proxy_id)
        if not proxy:
            return

        proxy.failure_count += 1
        proxy.health_score = max(0.0, proxy.health_score - 0.2)
        proxy.cooldown_until = time.time() + max(0.0, cooldown_seconds)

    def snapshot(self) -> List[Dict[str, object]]:
        """Return operational snapshot for metrics/debugging."""

        return [
            {
                "proxy_id": proxy.proxy_id,
                "server": proxy.server,
                "health_score": round(proxy.health_score, 2),
                "available": proxy.available,
                "failure_count": proxy.failure_count,
                "success_count": proxy.success_count,
            }
            for proxy in self.proxies
        ]

    def _find(self, proxy_id: str) -> Optional[ProxyEndpoint]:
        for proxy in self.proxies:
            if proxy.proxy_id == proxy_id:
                return proxy
        return None

    def _load_from_env(self) -> List[ProxyEndpoint]:
        """Load proxies from environment variables.

        Format:
        DIVAR_PROXY_LIST=proxy1.example.com:8080:user:pass,proxy2.example.com:8080
        """

        raw = os.getenv("DIVAR_PROXY_LIST", "").strip()
        if not raw:
            return []

        proxies: List[ProxyEndpoint] = []
        for index, item in enumerate(raw.split(",")):
            item = item.strip()
            if not item:
                continue

            parts = item.split(":")
            server = ""
            username = ""
            password = ""

            if len(parts) >= 2:
                server = f"http://{parts[0]}:{parts[1]}"
            if len(parts) >= 3:
                username = parts[2]
            if len(parts) >= 4:
                password = parts[3]

            if not server:
                continue

            proxies.append(
                ProxyEndpoint(
                    proxy_id=f"proxy-{index + 1}",
                    server=server,
                    username=username,
                    password=password,
                )
            )

        return proxies
