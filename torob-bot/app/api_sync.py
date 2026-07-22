import json
from typing import Any

import requests

from app.config import cfg


class ApiSync:
    def __init__(self) -> None:
        self.url = cfg.AFRAKALA_API_URL.rstrip("/") + "/leads/torob"
        self.token = cfg.AFRAKALA_API_KEY

    def sync(self, payload: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.token:
            return {"status": "skipped", "reason": "API key missing"}

        try:
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
            response = requests.post(self.url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            return {"status": "ok", "status_code": response.status_code, "response": response.text[:500]}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}
