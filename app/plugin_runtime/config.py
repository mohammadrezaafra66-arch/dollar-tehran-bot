from dataclasses import dataclass
import os


@dataclass(frozen=True)
class PluginRuntimeConfig:
    plugin_root_path: str = os.getenv(
        "AFRA_PLUGIN_ROOT_PATH",
        "plugins",
    )

    plugin_scan_interval_seconds: int = int(
        os.getenv(
            "AFRA_PLUGIN_SCAN_INTERVAL_SECONDS",
            "60",
        )
    )

    plugin_load_timeout_seconds: int = int(
        os.getenv(
            "AFRA_PLUGIN_LOAD_TIMEOUT_SECONDS",
            "15",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_PLUGIN_RUNTIME_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
