"""etcd coordination client for Afra Automation runtime.

This module provides a small, typed abstraction for leader election and
lease-based distributed coordination. It is intended for Kubernetes deployments
where multiple bot instances may run simultaneously and only one orchestrator
should own global scheduling decisions at a time.

The implementation imports etcd3 lazily so local development remains possible
without etcd installed.
"""

from __future__ import annotations

import os
import socket
import time
from dataclasses import dataclass
from typing import Optional


class EtcdUnavailable(RuntimeError):
    """Raised when etcd dependency or server is unavailable."""


@dataclass(frozen=True)
class EtcdSettings:
    """etcd connection and runtime coordination settings."""

    host: str
    port: int
    namespace: str
    instance_id: str
    leader_key: str
    default_ttl_seconds: int = 30

    @classmethod
    def from_env(cls) -> "EtcdSettings":
        """Build etcd settings from environment variables."""

        instance_id = os.getenv("DIVAR_BOT_INSTANCE_ID", socket.gethostname())
        namespace = os.getenv("AFRA_ETCD_NAMESPACE", "/afra/divar-bot")
        return cls(
            host=os.getenv("ETCD_HOST", "localhost"),
            port=int(os.getenv("ETCD_PORT", "2379")),
            namespace=namespace.rstrip("/"),
            instance_id=instance_id,
            leader_key=os.getenv("AFRA_LEADER_KEY", f"{namespace.rstrip('/')}/leader"),
            default_ttl_seconds=int(os.getenv("AFRA_ETCD_LEASE_TTL", "30")),
        )


@dataclass(frozen=True)
class DistributedLease:
    """A distributed lease returned by etcd."""

    key: str
    value: str
    lease_id: int
    ttl_seconds: int


class EtcdClient:
    """High-level etcd wrapper for distributed runtime coordination."""

    def __init__(self, settings: Optional[EtcdSettings] = None) -> None:
        self.settings = settings or EtcdSettings.from_env()
        self._client = None

    def _load_etcd3(self):
        """Import etcd3 lazily."""

        try:
            import etcd3  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise EtcdUnavailable("etcd3 package is not installed") from exc
        return etcd3

    @property
    def client(self):
        """Return cached etcd client."""

        if self._client is not None:
            return self._client

        etcd3 = self._load_etcd3()
        self._client = etcd3.client(host=self.settings.host, port=self.settings.port)
        return self._client

    def acquire_lease(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> Optional[DistributedLease]:
        """Acquire a distributed lease if the key does not already exist.

        Returns None when another instance already owns the key.
        """

        ttl = ttl_seconds or self.settings.default_ttl_seconds
        lease = self.client.lease(ttl)
        success, _ = self.client.transaction(
            compare=[self.client.transactions.version(key) == 0],
            success=[self.client.transactions.put(key, value, lease)],
            failure=[],
        )

        if not success:
            lease.revoke()
            return None

        return DistributedLease(key=key, value=value, lease_id=lease.id, ttl_seconds=ttl)

    def renew_lease_forever(self, lease: DistributedLease, stop_key: Optional[str] = None) -> None:
        """Keep a lease alive until process shutdown or optional stop key appears."""

        while True:
            if stop_key and self.get(stop_key):
                break
            self.client.refresh_lease(lease.lease_id)
            time.sleep(max(1, lease.ttl_seconds // 3))

    def elect_leader(self) -> Optional[DistributedLease]:
        """Try to become the active runtime orchestrator leader."""

        return self.acquire_lease(
            key=self.settings.leader_key,
            value=self.settings.instance_id,
            ttl_seconds=self.settings.default_ttl_seconds,
        )

    def current_leader(self) -> Optional[str]:
        """Return current leader instance id, if any."""

        return self.get(self.settings.leader_key)

    def get(self, key: str) -> Optional[str]:
        """Read a key as UTF-8 text."""

        value, _ = self.client.get(key)
        if value is None:
            return None
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)

    def put_state(self, name: str, value: str) -> None:
        """Store namespaced runtime state."""

        self.client.put(f"{self.settings.namespace}/{name.lstrip('/')}", value)

    def get_state(self, name: str) -> Optional[str]:
        """Read namespaced runtime state."""

        return self.get(f"{self.settings.namespace}/{name.lstrip('/')}")

    def release(self, lease: DistributedLease) -> None:
        """Release a distributed lease."""

        self.client.delete(lease.key)
        self.client.revoke_lease(lease.lease_id)
