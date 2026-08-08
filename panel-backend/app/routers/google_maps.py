from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.db_reader import google_maps_stats
from ..services.process_manager import get_logs, get_status, start_process, stop_process


router = APIRouter(prefix="/api/google-maps", tags=["GoogleMaps"])


class GoogleMapsStartRequest(BaseModel):
    query: str = Field(..., description="رشته جستجوی گوگل مپس")


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "panel-backend").exists():
            return parent
    return current.parents[3]


def _google_maps_output_dir() -> Path:
    return _repo_root() / "google-maps-bot" / "output"


@router.get("/stats")
async def stats_google_maps() -> dict:
    return google_maps_stats()


@router.get("/logs")
async def logs_google_maps(lines: int = Query(100, ge=1)) -> dict:
    entries = get_logs("google-maps", lines)
    return {"logs": entries}


@router.post("/start")
async def start_google_maps(request: GoogleMapsStartRequest) -> dict:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="فیلد query نمی‌تواند خالی باشد")

    cmd = ["python", "google-maps-bot/driver.py"]
    result = start_process("google-maps", cmd)
    return {"started": result.get("started", False), "pid": result.get("pid"), "cmd": result.get("cmd")}


@router.get("/status")
async def status_google_maps() -> dict:
    return get_status("google-maps")


@router.post("/stop")
async def stop_google_maps() -> dict:
    result = stop_process("google-maps")
    return {"stopped": result.get("stopped", False)}


@router.get("/exports")
async def exports_google_maps() -> dict:
    output_dir = _google_maps_output_dir()
    if not output_dir.exists():
        return {"files": []}

    files = sorted(str(path.name) for path in output_dir.glob("*.xlsx") if path.is_file())
    return {"files": files}
