from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]


def path_status(relative_path: str) -> dict:
    path = BASE_DIR / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "absolute_path": str(path),
    }


def rubika_module_status() -> dict:
    modules = [
        "app/rubika_adapter/config.py",
        "app/rubika_adapter/runtime.py",
        "app/rubika_adapter/retry_policy.py",
        "app/rubika_adapter/events.py",
        "app/sender_orchestration/config.py",
        "app/sender_orchestration/health_registry.py",
        "app/sender_orchestration/adaptive_router.py",
        "app/sender_orchestration/runtime_events.py",
        "app/session_orchestration/config.py",
        "app/session_orchestration/runtime.py",
        "app/session_orchestration/session_pool.py",
        "app/session_orchestration/events.py",
        "app/core/queue.py",
        "app/core/worker.py",
        "app/db/sqlite.py",
        "data/afra.db",
        "data/health.json",
        "app/event_store/store.py",
        "app/event_store/events.py",
        "app/schema_runtime/validation.py",
        "app/task_runtime/deduplication.py",
        "app/checkpoint_runtime/checkpoints.py",
        "app/voice_transcription/runtime.py",
        "app/ai_runtime/contracts.py",
        "app/ai_inference/runtime.py",
        "app/realtime_dashboard/runtime.py",
    ]
    return {"modules": [path_status(item) for item in modules]}
