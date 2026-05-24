from dataclasses import dataclass
import os


@dataclass(frozen=True)
class PlaywrightRuntimeConfig:
    browser_launch_timeout_seconds: int = int(
        os.getenv(
            "AFRA_PLAYWRIGHT_BROWSER_LAUNCH_TIMEOUT_SECONDS",
            "30",
        )
    )

    page_navigation_timeout_seconds: int = int(
        os.getenv(
            "AFRA_PLAYWRIGHT_PAGE_NAVIGATION_TIMEOUT_SECONDS",
            "45",
        )
    )

    max_parallel_browsers: int = int(
        os.getenv(
            "AFRA_PLAYWRIGHT_MAX_PARALLEL_BROWSERS",
            "5",
        )
    )

    headless_enabled: bool = (
        os.getenv(
            "AFRA_PLAYWRIGHT_HEADLESS_ENABLED",
            "true",
        ).lower()
        == "true"
    )
