"""Runtime orchestrator for Afra Automation Platform.

The orchestrator is the control-plane brain for distributed bot execution. It
turns metrics and topology into placement, scaling, throttling, and rebalance
plans without embedding business-specific crawling logic.

Design goals:
- policy-driven orchestration decisions
- shard-aware worker placement
- autoscaling recommendations for Kubernetes/HPA integration
- zero-downtime rebalance planning with draining first
- hot-partition detection
- structured decision objects suitable for logs, metrics, and audit trails

This module intentionally does not call Kubernetes directly. It produces safe,
traceable plans that can be applied by a deployment adapter later.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class OrchestratorPolicy:
    """Runtime orchestration thresholds and safety limits."""

    min_replicas: int
    max_replicas: int
    target_queue_per_worker: int
    max_failure_rate: float
    max_cpu_percent: float
    max_memory_percent: float
    hot_partition_multiplier: float
    rebalance_enabled: bool

    @classmethod
    def from_env(cls) -> "OrchestratorPolicy":
        """Load orchestration policy from environment variables."""

        return cls(
            min_replicas=int(os.getenv("AFRA_ORCH_MIN_REPLICAS", "1")),
            max_replicas=int(os.getenv("AFRA_ORCH_MAX_REPLICAS", "50")),
            target_queue_per_worker=int(os.getenv("AFRA_ORCH_TARGET_QUEUE_PER_WORKER", "100")),
            max_failure_rate=float(os.getenv("AFRA_ORCH_MAX_FAILURE_RATE", "0.15")),
            max_cpu_percent=float(os.getenv("AFRA_ORCH_MAX_CPU_PERCENT", "80")),
            max_memory_percent=float(os.getenv("AFRA_ORCH_MAX_MEMORY_PERCENT", "80")),
            hot_partition_multiplier=float(os.getenv("AFRA_ORCH_HOT_PARTITION_MULTIPLIER", "2.5")),
            rebalance_enabled=os.getenv("AFRA_ORCH_REBALANCE_ENABLED", "true").lower() == "true",
        )


@dataclass(frozen=True)
class WorkerNode:
    """Observed runtime state for one worker instance."""

    worker_id: str
    instance_id: str
    status: str
    active_jobs: int
    capacity: int
    cpu_percent: float
    memory_percent: float
    assigned_shards: Tuple[int, ...] = ()
    last_heartbeat_at: str = ""

    @property
    def available_capacity(self) -> int:
        """Return remaining job capacity for this worker."""

        return max(0, self.capacity - self.active_jobs)

    @property
    def is_healthy(self) -> bool:
        """Return whether the worker is eligible for new work."""

        return self.status == "active" and self.available_capacity > 0


@dataclass(frozen=True)
class ShardState:
    """Observed state for one queue shard or partition."""

    shard_id: int
    queue_depth: int
    inflight_jobs: int
    failure_rate: float
    owner_worker_id: Optional[str] = None


@dataclass(frozen=True)
class PlacementDecision:
    """Assignment decision for a shard."""

    shard_id: int
    worker_id: Optional[str]
    reason: str


@dataclass(frozen=True)
class AutoscalingDecision:
    """Desired replica count and reason."""

    current_replicas: int
    desired_replicas: int
    reason: str


@dataclass(frozen=True)
class RebalanceAction:
    """A safe rebalance action that can be applied by an adapter."""

    action: str
    shard_id: int
    from_worker_id: Optional[str]
    to_worker_id: Optional[str]
    reason: str


@dataclass(frozen=True)
class OrchestrationPlan:
    """Full orchestration output for one control loop iteration."""

    created_at: str
    placements: List[PlacementDecision] = field(default_factory=list)
    autoscaling: Optional[AutoscalingDecision] = None
    rebalance_actions: List[RebalanceAction] = field(default_factory=list)
    throttled_shards: List[int] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RuntimeOrchestrator:
    """Policy-driven runtime orchestrator for distributed bot workers."""

    def __init__(self, policy: Optional[OrchestratorPolicy] = None) -> None:
        self.policy = policy or OrchestratorPolicy.from_env()

    def build_plan(
        self,
        workers: Iterable[WorkerNode],
        shards: Iterable[ShardState],
        current_replicas: int,
    ) -> OrchestrationPlan:
        """Build one orchestration plan from observed worker/shard state."""

        worker_list = list(workers)
        shard_list = list(shards)
        placements = self.plan_placements(worker_list, shard_list)
        autoscaling = self.plan_autoscaling(worker_list, shard_list, current_replicas)
        rebalance_actions = self.plan_rebalance(worker_list, shard_list)
        throttled_shards = self.detect_throttled_shards(shard_list)
        warnings = self.detect_warnings(worker_list, shard_list)

        return OrchestrationPlan(
            created_at=datetime.utcnow().isoformat(),
            placements=placements,
            autoscaling=autoscaling,
            rebalance_actions=rebalance_actions,
            throttled_shards=throttled_shards,
            warnings=warnings,
        )

    def plan_placements(self, workers: List[WorkerNode], shards: List[ShardState]) -> List[PlacementDecision]:
        """Assign unowned shards to the healthiest available workers."""

        healthy_workers = sorted(
            [worker for worker in workers if worker.is_healthy],
            key=lambda item: (item.memory_percent, item.cpu_percent, item.active_jobs),
        )
        decisions: List[PlacementDecision] = []

        for shard in shards:
            if shard.owner_worker_id:
                decisions.append(PlacementDecision(shard.shard_id, shard.owner_worker_id, "already_owned"))
                continue

            if not healthy_workers:
                decisions.append(PlacementDecision(shard.shard_id, None, "no_healthy_worker"))
                continue

            selected = healthy_workers[0]
            decisions.append(PlacementDecision(shard.shard_id, selected.worker_id, "least_loaded_healthy_worker"))
            healthy_workers = sorted(
                healthy_workers,
                key=lambda item: (item.worker_id == selected.worker_id, item.memory_percent, item.cpu_percent),
            )

        return decisions

    def plan_autoscaling(
        self,
        workers: List[WorkerNode],
        shards: List[ShardState],
        current_replicas: int,
    ) -> AutoscalingDecision:
        """Calculate desired replica count from queue pressure and worker health."""

        total_queue = sum(shard.queue_depth for shard in shards)
        unhealthy_workers = [worker for worker in workers if worker.status != "active"]
        overloaded_workers = [
            worker
            for worker in workers
            if worker.cpu_percent >= self.policy.max_cpu_percent or worker.memory_percent >= self.policy.max_memory_percent
        ]

        desired = max(self.policy.min_replicas, current_replicas)
        reason = "stable"

        if total_queue > 0:
            queue_based = max(self.policy.min_replicas, (total_queue // self.policy.target_queue_per_worker) + 1)
            if queue_based > desired:
                desired = queue_based
                reason = "queue_pressure"

        if overloaded_workers:
            desired = max(desired, current_replicas + 1)
            reason = "worker_resource_pressure"

        if unhealthy_workers:
            desired = max(desired, current_replicas)
            reason = "unhealthy_workers_detected"

        if total_queue == 0 and not overloaded_workers and current_replicas > self.policy.min_replicas:
            desired = max(self.policy.min_replicas, current_replicas - 1)
            reason = "scale_down_idle"

        desired = min(self.policy.max_replicas, max(self.policy.min_replicas, desired))
        return AutoscalingDecision(current_replicas=current_replicas, desired_replicas=desired, reason=reason)

    def plan_rebalance(self, workers: List[WorkerNode], shards: List[ShardState]) -> List[RebalanceAction]:
        """Plan safe shard movement away from overloaded or unhealthy workers."""

        if not self.policy.rebalance_enabled:
            return []

        worker_by_id = {worker.worker_id: worker for worker in workers}
        targets = sorted(
            [worker for worker in workers if worker.is_healthy],
            key=lambda item: (item.active_jobs, item.memory_percent, item.cpu_percent),
        )
        actions: List[RebalanceAction] = []

        for shard in shards:
            if not shard.owner_worker_id:
                continue

            owner = worker_by_id.get(shard.owner_worker_id)
            owner_bad = (
                owner is None
                or owner.status != "active"
                or owner.cpu_percent >= self.policy.max_cpu_percent
                or owner.memory_percent >= self.policy.max_memory_percent
                or shard.failure_rate >= self.policy.max_failure_rate
            )

            if not owner_bad:
                continue

            target = next((candidate for candidate in targets if candidate.worker_id != shard.owner_worker_id), None)
            if not target:
                actions.append(
                    RebalanceAction("drain_only", shard.shard_id, shard.owner_worker_id, None, "no_safe_target")
                )
                continue

            actions.append(
                RebalanceAction("drain_then_move", shard.shard_id, shard.owner_worker_id, target.worker_id, "owner_unhealthy_or_hot")
            )

        return actions

    def detect_throttled_shards(self, shards: List[ShardState]) -> List[int]:
        """Return shards that should be throttled due to high failure rate."""

        return [shard.shard_id for shard in shards if shard.failure_rate >= self.policy.max_failure_rate]

    def detect_hot_partitions(self, shards: List[ShardState]) -> List[int]:
        """Detect queue shards significantly hotter than average."""

        if not shards:
            return []
        average_depth = sum(shard.queue_depth for shard in shards) / len(shards)
        if average_depth <= 0:
            return []
        return [
            shard.shard_id
            for shard in shards
            if shard.queue_depth >= average_depth * self.policy.hot_partition_multiplier
        ]

    def detect_warnings(self, workers: List[WorkerNode], shards: List[ShardState]) -> List[str]:
        """Generate human-readable warnings for logs and dashboards."""

        warnings: List[str] = []
        hot = self.detect_hot_partitions(shards)
        if hot:
            warnings.append(f"hot_partitions_detected:{hot}")

        no_owner = [shard.shard_id for shard in shards if not shard.owner_worker_id]
        if no_owner:
            warnings.append(f"unowned_shards:{no_owner}")

        unhealthy = [worker.worker_id for worker in workers if worker.status != "active"]
        if unhealthy:
            warnings.append(f"unhealthy_workers:{unhealthy}")

        return warnings
