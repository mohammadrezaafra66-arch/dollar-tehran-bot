# app/browser_factory.py
"""Browser launch helpers for local Windows execution.

Playwright's bundled Chromium may fail to download in some locations. This helper
first tries installed Chrome/Edge from the local machine, then falls back to the
Playwright-managed Chromium if available.
"""

from __future__ import annotations

import os
from typing import Optional

from app.config import Config


LOCAL_BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_local_browser() -> Optional[str]:
    env_path = os.environ.get("GOOGLE_MAPS_BOT_BROWSER") or os.environ.get("CHROME_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    for path in LOCAL_BROWSER_CANDIDATES:
        if os.path.exists(path):
            return path

    return None


def launch_chromium(p):
    """Launch a Chromium-compatible browser for the bot."""
    local_browser = find_local_browser()
    launch_kwargs = {
        "headless": Config.HEADLESS,
        "slow_mo": Config.SLOW_MO,
    }

    if local_browser:
        print(f"🌐 Using local browser: {local_browser}")
        launch_kwargs["executable_path"] = local_browser
    else:
        print("🌐 Local Chrome/Edge not found; using Playwright bundled Chromium")

    return p.chromium.launch(**launch_kwargs)
