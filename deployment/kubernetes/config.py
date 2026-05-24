from dataclasses import dataclass
import os


@dataclass(frozen=True)
class KubernetesRuntimeConfig:
    namespace: str = os.getenv(
        "AFRA_KUBERNETES_NAMESPACE",
        "afra-production",
    )

    deployment_timeout_seconds: int = int(
        os.getenv(
            "AFRA_KUBERNETES_DEPLOYMENT_TIMEOUT_SECONDS",
            "300",
        )
    )

    max_parallel_rollouts: int = int(
        os.getenv(
            "AFRA_KUBERNETES_MAX_PARALLEL_ROLLOUTS",
            "5",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_KUBERNETES_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
