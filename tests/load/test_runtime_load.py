"""Lightweight runtime load tests.

These tests are intentionally conservative so they can run in CI. Their goal is
not benchmarking absolute throughput, but validating that runtime orchestration
logic behaves consistently under moderate pressure.
"""

from __future__ import annotations

from divar_bot.orchestrator.runtime_orchestrator import (
    RuntimeOrchestrator,
    ShardState,
    WorkerNode,
)


def test_runtime_orchestrator_balances_load() -> None:
    """The orchestrator should produce placements and scaling decisions under load."""

    orchestrator = RuntimeOrchestrator()

    workers = [
        WorkerNode(
            worker_id=f"worker-{index}",
            instance_id=f"instance-{index}",
            status="active",
            active_jobs=5 + index,
            capacity=20,
            cpu_percent=40,
            memory_percent=45,
        )
        for index in range(5)
    ]

    shards = [
        ShardState(
            shard_id=index,
            queue_depth=100 + (index * 25),
            inflight_jobs=5,
            failure_rate=0.01,
            owner_worker_id=None,
        )
        for index in range(12)
    ]

    plan = orchestrator.build_plan(
        workers=workers,
        shards=shards,
        current_replicas=5,
    )

    assert plan.autoscaling is not None
    assert plan.autoscaling.desired_replicas >= 5
    assert len(plan.placements) == len(shards)


def test_hot_partition_detection() -> None:
    """Hot shards should be detectable under skewed queue pressure."""

    orchestrator = RuntimeOrchestrator()

    shards = [
        ShardState(
            shard_id=1,
            queue_depth=100,
            inflight_jobs=3,
            failure_rate=0.0,
        ),
        ShardState(
            shard_id=2,
            queue_depth=900,
            inflight_jobs=8,
            failure_rate=0.0,
        ),
        ShardState(
            shard_id=3,
            queue_depth=120,
            inflight_jobs=4,
            failure_rate=0.0,
        ),
    ]

    hot = orchestrator.detect_hot_partitions(shards)

    assert 2 in hot
