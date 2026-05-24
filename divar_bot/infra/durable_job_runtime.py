"""Durable distributed job runtime for Afra Automation.

This module wires together Kafka, WAL recovery, idempotency, retry/DLQ routing,
rate limiting, and structured runtime decisions. It is intentionally thin and
composable: extraction logic remains in workers/plugins while this layer owns
safe delivery semantics.

Processing contract:
1. Receive event from Kafka.
2. Append job_received to WAL before doing work.
3. Check idempotency before executing.
4. Apply distributed rate limit policy.
5. Execute handler.
6. Append job_completed/job_failed to WAL.
7. Commit Kafka offset only after durable success or durable retry/DLQ routing.

This does not claim true global exactly-once semantics. It provides practical
at-least-once delivery with idempotent processing protection, which is the sane
production baseline for crawler workloads.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

from divar_bot.infra.distributed_rate_limiter import DistributedRateLimiter, RateLimitPolicy
from divar_bot.infra.kafka_adapter import KafkaAdapter, QueueEvent
from divar_bot.infra.wal_recovery import WalRecord, WalRecovery


class DurableJobRuntimeError(RuntimeError):
    """Base error for durable job runtime failures."""


@dataclass(frozen=True)
class RetryPolicy:
    """Retry routing policy for failed jobs."""

    max_attempts: int
    base_delay_seconds: float
    max_delay_seconds: float
    jitter_seconds: float

    @classmethod
    def from_env(cls) -> "RetryPolicy":
        """Load retry policy from environment variables."""

        return cls(
            max_attempts=int(os.getenv("AFRA_JOB_MAX_ATTEMPTS", "3")),
            base_delay_seconds=float(os.getenv("AFRA_JOB_RETRY_BASE_DELAY", "30")),
            max_delay_seconds=float(os.getenv("AFRA_JOB_RETRY_MAX_DELAY", "900")),
            jitter_seconds=float(os.getenv("AFRA_JOB_RETRY_JITTER", "5")),
        )

    def delay_for_attempt(self, attempt: int) -> float:
        """Return bounded exponential backoff delay."""

        delay = self.base_delay_seconds * (2 ** max(0, attempt - 1))
        return min(delay + self.jitter_seconds, self.max_delay_seconds)


@dataclass(frozen=True)
class JobRuntimeDecision:
    """A structured decision suitable for logs and metrics."""

    event_id: str
    trace_id: str
    action: str
    reason: str
    committed: bool = False
    retry_delay_seconds: float = 0.0


class RedisIdempotencyStore:
    """Small Redis-backed idempotency store with local-safe lazy import."""

    def __init__(self, redis_url: Optional[str] = None, namespace: str = "afra:idempotency") -> None:
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.namespace = namespace
        self._redis = None

    def _client(self):
        if self._redis is not None:
            return self._redis
        import redis  # type: ignore

        self._redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
        self._redis.ping()
        return self._redis

    def key(self, event_id: str) -> str:
        """Build Redis key for an event id."""

        return f"{self.namespace}:{event_id}"

    def already_processed(self, event_id: str) -> bool:
        """Return whether an event has already been processed."""

        try:
            return bool(self._client().exists(self.key(event_id)))
        except Exception:
            return False

    def mark_processed(self, event_id: str, ttl_seconds: int = 86400) -> None:
        """Mark event as processed."""

        try:
            self._client().set(self.key(event_id), "processed", ex=ttl_seconds)
        except Exception:
            return


class DurableJobRuntime:
    """Coordinates safe distributed job execution around a user handler."""

    def __init__(
        self,
        kafka: Optional[KafkaAdapter] = None,
        wal: Optional[WalRecovery] = None,
        idempotency: Optional[RedisIdempotencyStore] = None,
        rate_limiter: Optional[DistributedRateLimiter] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> None:
        self.kafka = kafka or KafkaAdapter()
        self.wal = wal or WalRecovery()
        self.idempotency = idempotency or RedisIdempotencyStore()
        self.rate_limiter = rate_limiter or DistributedRateLimiter()
        self.retry_policy = retry_policy or RetryPolicy.from_env()

    def process_event(
        self,
        event: QueueEvent,
        handler: Callable[[QueueEvent], None],
        domain: str,
        identity: str = "global",
    ) -> JobRuntimeDecision:
        """Process one event with WAL/idempotency/rate-limit protection."""

        attempt = int(event.headers.get("attempt", "1"))
        self.wal.append(
            WalRecord(
                event_id=event.event_id,
                event_type="job_received",
                payload={"event_type": event.event_type, "attempt": attempt},
                trace_id=event.trace_id,
            )
        )

        if self.idempotency.already_processed(event.event_id):
            self.wal.append(
                WalRecord(
                    event_id=f"{event.event_id}:duplicate",
                    event_type="job_duplicate_skipped",
                    payload={"event_id": event.event_id},
                    trace_id=event.trace_id,
                )
            )
            self.kafka.commit()
            return JobRuntimeDecision(event.event_id, event.trace_id, "skip", "already_processed", committed=True)

        limit_decision = self.rate_limiter.acquire(
            domain=domain,
            identity=identity,
            action=event.event_type,
            policy=RateLimitPolicy.from_env("AFRA_JOB_RATE_LIMIT"),
        )
        if not limit_decision.allowed:
            retry_event = self._with_attempt(event, attempt)
            self.kafka.publish_retry(retry_event, reason="rate_limited")
            self.wal.append(
                WalRecord(
                    event_id=f"{event.event_id}:rate_limited",
                    event_type="job_retry_scheduled",
                    payload={"reason": "rate_limited", "retry_after_seconds": limit_decision.retry_after_seconds},
                    trace_id=event.trace_id,
                )
            )
            self.kafka.commit()
            return JobRuntimeDecision(
                event.event_id,
                event.trace_id,
                "retry",
                "rate_limited",
                committed=True,
                retry_delay_seconds=limit_decision.retry_after_seconds,
            )

        try:
            handler(event)
            self.idempotency.mark_processed(event.event_id)
            self.wal.append(
                WalRecord(
                    event_id=f"{event.event_id}:completed",
                    event_type="job_completed",
                    payload={"attempt": attempt},
                    trace_id=event.trace_id,
                )
            )
            self.kafka.commit()
            return JobRuntimeDecision(event.event_id, event.trace_id, "complete", "handler_success", committed=True)
        except Exception as exc:
            return self._handle_failure(event, attempt, exc)

    def _handle_failure(self, event: QueueEvent, attempt: int, exc: Exception) -> JobRuntimeDecision:
        """Route failed event to retry or dead-letter topic and commit after durable routing."""

        reason = f"{type(exc).__name__}: {str(exc)[:300]}"
        self.wal.append(
            WalRecord(
                event_id=f"{event.event_id}:failed:{attempt}",
                event_type="job_failed",
                payload={"attempt": attempt, "reason": reason},
                trace_id=event.trace_id,
            )
        )

        if attempt >= self.retry_policy.max_attempts:
            self.kafka.publish_dead_letter(event, reason=reason)
            self.wal.append(
                WalRecord(
                    event_id=f"{event.event_id}:dead_lettered",
                    event_type="job_dead_lettered",
                    payload={"attempt": attempt, "reason": reason},
                    trace_id=event.trace_id,
                )
            )
            self.kafka.commit()
            return JobRuntimeDecision(event.event_id, event.trace_id, "dead_letter", reason, committed=True)

        delay = self.retry_policy.delay_for_attempt(attempt)
        retry_event = self._with_attempt(event, attempt + 1)
        retry_event.headers["retry_delay_seconds"] = str(delay)
        self.kafka.publish_retry(retry_event, reason=reason)
        self.wal.append(
            WalRecord(
                event_id=f"{event.event_id}:retry:{attempt + 1}",
                event_type="job_retry_scheduled",
                payload={"next_attempt": attempt + 1, "delay_seconds": delay, "reason": reason},
                trace_id=event.trace_id,
            )
        )
        self.kafka.commit()
        return JobRuntimeDecision(event.event_id, event.trace_id, "retry", reason, committed=True, retry_delay_seconds=delay)

    def _with_attempt(self, event: QueueEvent, attempt: int) -> QueueEvent:
        """Clone an event while updating attempt metadata."""

        return QueueEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload,
            trace_id=event.trace_id,
            created_at=event.created_at,
            headers={**event.headers, "attempt": str(attempt), "routed_at": str(time.time())},
        )
