from dataclasses import dataclass
import os


@dataclass(frozen=True)
class IntegrationHarnessConfig:
    test_timeout_seconds: int = int(
        os.getenv(
            "AFRA_INTEGRATION_TEST_TIMEOUT_SECONDS",
            "30",
        )
    )

    max_parallel_tests: int = int(
        os.getenv(
            "AFRA_MAX_PARALLEL_INTEGRATION_TESTS",
            "5",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_INTEGRATION_HARNESS_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
