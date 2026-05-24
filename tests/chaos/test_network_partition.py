"""Chaos tests for short network partition scenarios.

These tests validate that the durable runtime does not commit Kafka offsets before
job state has been durably routed to success, retry, or dead-letter paths.
They use lightweight fakes so they can run in CI without Kafka, Redis, or etcd.
"""

from __future__ import annotations

from typing import List

import pytest

from divar_bot.infra.durable_job_runtime import DurableJobRuntime, RedisIdempotencyStore, RetryPolicy
from divar_bot.infra.kafka_adapter import QueueEvent
from divar_bot.infra.wal_recovery import WalRecovery, WalSettings
from divar_bot.infra.distributed_rate_limiter import RateLimitDecision


class FakeKafka:
    """Minimal Kafka fake for runtime contract tests."""

    def __init__(self) -> None:
        self.commits = 0
        self.retries: List[QueueEvent] = []
        self.dead_letters: List[QueueEvent] = []

    def commit(self) -> None:
        self.commits += 1

    def publish_retry(self, event: QueueEvent, reason: str) -> None:
        self.retries.append(event)

    def publish_dead_letter(self, event: QueueEvent, reason: str) -> None:
        self.dead_letters.append(event)


class FakeIdempotency(RedisIdempotencyStore):
    """In-memory idempotency fake."""

    def __init__(self) -> None:
        self.processed = set()

    def already_processed(self, event_id: str) -> bool:
        return event_id in self.processed

    def mark_processed(self, event_id: str, ttl_seconds: int = 86400) -> None:
        self.processed.add(event_id)


class FakeRateLimiter:
    """Rate limiter fake that always allows."""

    def acquire(self, *args, **kwargs) -> RateLimitDecision:
        return RateLimitDecision(True, 0.0, "fake", 1.0, "allowed")


def make_event() -> QueueEvent:
    """Create a stable test event."""

    return QueueEvent(
        event_id="evt-network-partition",
        event_type="divar.extract",
        payload={"url": "https://example.test/item/1"},
        trace_id="trace-network-partition",
        headers={"attempt": "1"},
    )


def test_network_partition_routes_to_retry_before_commit(tmp_path) -> None:
    """A transient network failure must be retried and then offset committed."""

    kafka = FakeKafka()
    wal = WalRecovery(
        WalSettings(
            wal_path=tmp_path / "runtime.wal.jsonl",
            snapshot_path=tmp_path / "snapshot.json",
            fsync=False,
        )
    )
    runtime = DurableJobRuntime(
        kafka=kafka,  # type: ignore[arg-type]
        wal=wal,
        idempotency=FakeIdempotency(),
        rate_limiter=FakeRateLimiter(),  # type: ignore[arg-type]
        retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=1, max_delay_seconds=5, jitter_seconds=0),
    )

    def handler(_: QueueEvent) -> None:
        raise TimeoutError("simulated 3 second network partition")

    decision = runtime.process_event(make_event(), handler, domain="divar.ir", identity="worker-1")

    assert decision.action == "retry"
    assert kafka.commits == 1
    assert len(kafka.retries) == 1
    assert len(kafka.dead_letters) == 0

    replayed = list(wal.replay(stop_on_corruption=True))
    assert any(record.event_type == "job_received" for record in replayed)
    assert any(record.event_type == "job_failed" for record in replayed)
    assert any(record.event_type == "job_retry_scheduled" for record in replayed)


def test_network_partition_after_max_attempts_goes_to_dlq(tmp_path) -> None:
    """A repeated network partition must be quarantined in DLQ after max attempts."""

    kafka = FakeKafka()
    wal = WalRecovery(
        WalSettings(
            wal_path=tmp_path / "runtime.wal.jsonl",
            snapshot_path=tmp_path / "snapshot.json",
            fsync=False,
        )
    )
    runtime = DurableJobRuntime(
        kafka=kafka,  # type: ignore[arg-type]
        wal=wal,
        idempotency=FakeIdempotency(),
        rate_limiter=FakeRateLimiter(),  # type: ignore[arg-type]
        retry_policy=RetryPolicy(max_attempts=1, base_delay_seconds=1, max_delay_seconds=5, jitter_seconds=0),
    )

    def handler(_: QueueEvent) -> None:
        raise ConnectionError("simulated network partition")

    decision = runtime.process_event(make_event(), handler, domain="divar.ir", identity="worker-1")

    assert decision.action == "dead_letter"
    assert kafka.commits == 1
    assert len(kafka.retries) == 0
    assert len(kafka.dead_letters) == 1

    replayed = list(wal.replay(stop_on_corruption=True))
    assert any(record.event_type == "job_dead_lettered" for record in replayed)
