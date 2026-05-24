import json
import os
from datetime import datetime


def write_health(path="data/health.json", status="ok", details=None):
    details = details or {}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "status": status,
        "details": details,
        "updated_at": datetime.utcnow().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return payload
