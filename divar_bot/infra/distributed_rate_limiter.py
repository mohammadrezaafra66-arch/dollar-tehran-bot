"""Distributed rate limiter for Afra Automation runtime.

This module protects upstream sources from burst traffic when many bot instances
run at the same time. It uses a Redis-backed token bucket when Redis is
available and falls back to a local in-memory limiter for development.

Design goals:
- config-driven limits
- per-domain and per-identity buckets
- safe defaults for 50+ instances
- no hard-coded sleep behavior in business logic
- observable decision output for logs and metrics
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional, Tuple


class RateLimiterUnavailable(RuntimeError):
    """Raised when the distributed limiter backend is unavailable."""


@dataclass(frozen=True)
class RateLimitDecision:
    """Result of a rate-limit check."""

    allowed: bool
    retry_after_seconds: float
    bucket_key: str
    remaining_tokens: float
    reason: str


@dataclass(frozen=True)
class RateLimitPolicy:
    """Token-bucket policy for one logical traffic class."""

    capacity: int
    refill_per_second: float

    @classmethod
    def from_env(cls, prefix: str = "AFRA_RATE_LIMIT") -> "RateLimitPolicy":
        """Build policy from environment variables."""

        return cls(
            capacity=int(os.getenv(f"{prefix}_CAPACITY", "30")),
            refill_per_second=float(os.getenv(f"{prefix}_REFILL_PER_SECOND", "0.5")),
        )


@dataclass(frozen=True)
class RateLimiterSettings:
    """Settings for Redis-backed distributed rate limiting."""

    redis_url: str
    namespace: str
    default_policy: RateLimitPolicy
    local_fallback_enabled: bool = True

    @classmethod
    def from_env(cls) -> "RateLimiterSettings":
        """Load limiter settings from environment variables."""

        return cls(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            namespace=os.getenv("AFRA_RATE_LIMIT_NAMESPACE", "afra:rate-limit"),
            default_policy=RateLimitPolicy.from_env(),
            local_fallback_enabled=os.getenv("AFRA_RATE_LIMIT_LOCAL_FALLBACK", "true").lower() == "true",
        )


class LocalTokenBucket:
    """Thread-safe local token bucket fallback."""

    def __init__(self) -> None:
        self._state: Dict[str, Tuple[float, float]] = {}
        self._lock = Lock()

    def acquire(self, bucket_key: str, policy: RateLimitPolicy, tokens: int = 1) -> RateLimitDecision:
        """Acquire tokens from the local bucket."""

        now = time.monotonic()
        with self._lock:
            current_tokens, last_refill = self._state.get(bucket_key, (float(policy.capacity), now))
            elapsed = max(0.0, now - last_refill)
            current_tokens = min(float(policy.capacity), current_tokens + elapsed * policy.refill_per_second)

            if current_tokens >= tokens:
                current_tokens -= tokens
                self._state[bucket_key] = (current_tokens, now)
                return RateLimitDecision(True, 0.0, bucket_key, current_tokens, "local_allowed")

            missing = tokens - current_tokens
            retry_after = missing / policy.refill_per_second if policy.refill_per_second > 0 else 60.0
            self._state[bucket_key] = (current_tokens, now)
            return RateLimitDecision(False, retry_after, bucket_key, current_tokens, "local_limited")


class DistributedRateLimiter:
    """Redis-backed distributed token bucket with local fallback."""

    _LUA_TOKEN_BUCKET = """
local bucket_key = KEYS[1]
local now = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local refill_per_second = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
local ttl_seconds = tonumber(ARGV[5])

local bucket = redis.call('HMGET', bucket_key, 'tokens', 'updated_at')
local tokens = tonumber(bucket[1])
local updated_at = tonumber(bucket[2])

if tokens == nil then
  tokens = capacity
  updated_at = now
end

local elapsed = math.max(0, now - updated_at)
tokens = math.min(capacity, tokens + (elapsed * refill_per_second))

if tokens >= requested then
  tokens = tokens - requested
  redis.call('HMSET', bucket_key, 'tokens', tokens, 'updated_at', now)
  redis.call('EXPIRE', bucket_key, ttl_seconds)
  return {1, 0, tokens}
end

local missing = requested - tokens
local retry_after = 60
if refill_per_second > 0 then
  retry_after = missing / refill_per_second
end

redis.call('HMSET', bucket_key, 'tokens', tokens, 'updated_at', now)
redis.call('EXPIRE', bucket_key, ttl_seconds)
return {0, retry_after, tokens}
"""

    def __init__(self, settings: Optional[RateLimiterSettings] = None) -> None:
        self.settings = settings or RateLimiterSettings.from_env()
        self._redis = None
        self._local = LocalTokenBucket()

    def _connect_redis(self):
        """Connect to Redis lazily."""

        if self._redis is not None:
            return self._redis

        try:
            import redis  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RateLimiterUnavailable("redis package is not installed") from exc

        self._redis = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)
        self._redis.ping()
        return self._redis

    def bucket_key(self, domain: str, identity: str = "global", action: str = "request") -> str:
        """Build stable bucket key for a domain/identity/action tuple."""

        normalized_domain = domain.lower().replace("https://", "").replace("http://", "").strip("/")
        normalized_identity = identity.lower().strip() or "global"
        normalized_action = action.lower().strip() or "request"
        return f"{self.settings.namespace}:{normalized_domain}:{normalized_identity}:{normalized_action}"

    def acquire(
        self,
        domain: str,
        identity: str = "global",
        action: str = "request",
        tokens: int = 1,
        policy: Optional[RateLimitPolicy] = None,
    ) -> RateLimitDecision:
        """Try to acquire tokens from the distributed limiter."""

        effective_policy = policy or self.settings.default_policy
        key = self.bucket_key(domain=domain, identity=identity, action=action)

        try:
            redis_client = self._connect_redis()
            ttl_seconds = max(60, int((effective_policy.capacity / max(effective_policy.refill_per_second, 0.01)) * 2))
            allowed, retry_after, remaining = redis_client.eval(
                self._LUA_TOKEN_BUCKET,
                1,
                key,
                time.time(),
                effective_policy.capacity,
                effective_policy.refill_per_second,
                tokens,
                ttl_seconds,
            )
            return RateLimitDecision(
                allowed=bool(int(allowed)),
                retry_after_seconds=float(retry_after),
                bucket_key=key,
                remaining_tokens=float(remaining),
                reason="redis_allowed" if int(allowed) else "redis_limited",
            )
        except Exception:
            if not self.settings.local_fallback_enabled:
                raise
            return self._local.acquire(key, effective_policy, tokens=tokens)

    def wait_if_needed(self, decision: RateLimitDecision, max_wait_seconds: Optional[float] = None) -> None:
        """Sleep only when a caller explicitly decides to honor limiter delay."""

        if decision.allowed:
            return
        wait_seconds = decision.retry_after_seconds
        if max_wait_seconds is not None:
            wait_seconds = min(wait_seconds, max_wait_seconds)
        time.sleep(max(0.0, wait_seconds))
