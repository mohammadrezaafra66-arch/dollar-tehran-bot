from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Query

from ..services.config_manager import read_torob_config, write_config
from ..services.db_reader import torob_reports, torob_seller_detail, torob_sellers, torob_stats
from ..services.process_manager import _repo_root, get_logs, get_status, start_process, stop_process

router = APIRouter(prefix="/api/torob", tags=["Torob"])


@router.get("/stats")
async def get_torob_stats() -> dict:
    return torob_stats()


@router.get("/sellers")
async def get_torob_sellers(
    limit: Annotated[int, Query()] = 100,
    offset: Annotated[int, Query()] = 0,
    crawl_status: Annotated[str | None, Query()] = None,
) -> dict:
    return torob_sellers(limit=limit, offset=offset, crawl_status=crawl_status)


@router.get("/sellers/{id}")
async def get_torob_seller_detail(id: Annotated[int, FastAPIPath()]) -> dict:
    item = torob_seller_detail(id)
    if item is None:
        raise HTTPException(status_code=404, detail="فروشنده یافت نشد")
    return item


@router.get("/reports")
async def get_torob_reports(
    limit: Annotated[int, Query()] = 100,
    offset: Annotated[int, Query()] = 0,
) -> dict:
    return torob_reports(limit=limit, offset=offset)


@router.get("/logs")
async def get_torob_process_logs(lines: Annotated[int, Query()] = 100) -> dict:
    return {"lines": get_logs("torob", lines)}


@router.post("/run")
async def run_torob(payload: dict) -> dict:
    query = str(payload.get("query", "")).strip()
    cmd = ["python", "torob-bot/driver.py", "--mode", "run", "--query", query]
    return start_process("torob", cmd)


@router.get("/run/status")
async def get_torob_run_status() -> dict:
    return get_status("torob")


@router.post("/run/stop")
async def stop_torob_run() -> dict:
    return stop_process("torob")


@router.get("/config")
async def get_torob_config() -> dict:
    return read_torob_config()


@router.post("/config")
async def save_torob_config(payload: dict) -> dict:
    return {"saved": write_config("torob", payload)}


@router.get("/exports")
async def list_torob_exports() -> dict:
    output_dir = _repo_root() / "torob-bot" / "output"
    if not output_dir.exists():
        return {"items": []}

    items = []
    for path in sorted(output_dir.glob("*.xlsx"), key=lambda item: item.name):
        stat = path.stat()
        items.append(
            {
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )
    return {"items": items}


@router.get("/export")
async def get_latest_torob_export() -> dict:
    output_dir = _repo_root() / "torob-bot" / "output"
    if not output_dir.exists():
        return {"file": ""}

    files = sorted(output_dir.glob("*.xlsx"), key=lambda item: item.stat().st_mtime, reverse=True)
    return {"file": files[0].name if files else ""}
