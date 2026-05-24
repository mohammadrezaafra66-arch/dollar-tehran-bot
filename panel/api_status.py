from __future__ import annotations


def health_payload() -> dict:
    return {"status": "ok", "service": "local-panel"}


def idle_bot_status(bot_id: str, bot_name: str | None = None) -> dict:
    return {
        "found": True,
        "bot_id": bot_id,
        "name": bot_name,
        "status": "idle",
        "current_job_id": None,
        "success": 0,
        "failed": 0,
    }
