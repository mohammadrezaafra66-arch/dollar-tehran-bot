from __future__ import annotations

from dataclasses import dataclass
import os


def _bool_env(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() == "true"


@dataclass(frozen=True)
class SessionGovernanceConfig:
    risk_threshold: float = float(
        os.getenv("AFRA_SESSION_RISK_THRESHOLD", "0.70")
    )
    cooldown_seconds: int = int(
        os.getenv("AFRA_SESSION_COOLDOWN_SECONDS", "1800")
    )
    max_parallel_actions: int = int(
        os.getenv("AFRA_SESSION_MAX_PARALLEL_ACTIONS", "2")
    )
    trust_decay_step: float = float(
        os.getenv("AFRA_SESSION_TRUST_DECAY_STEP", "0.05")
    )
    trust_recovery_step: float = float(
        os.getenv("AFRA_SESSION_TRUST_RECOVERY_STEP", "0.02")
    )
    degraded_mode_enabled: bool = _bool_env(
        "AFRA_SESSION_GOVERNANCE_DEGRADED_MODE_ENABLED",
        "true",
    )
    max_event_window: int = int(
        os.getenv("AFRA_SESSION_EVENT_WINDOW", "100")
    )


config = SessionGovernanceConfig()
