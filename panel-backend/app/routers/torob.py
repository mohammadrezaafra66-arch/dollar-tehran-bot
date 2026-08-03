from fastapi import APIRouter
from ..services.bot_manager import BotManager
from ..models.schemas import BotStartRequest

router = APIRouter(prefix="/api/torob", tags=["Torob"])
manager = BotManager()


@router.post("/start")
async def start_torob(params: BotStartRequest):
    return await manager.start_bot("torob", params.model_dump())


@router.post("/stop")
async def stop_torob():
    return await manager.stop_bot("torob")


@router.get("/status")
async def get_torob_status():
    return await manager.get_status("torob")


@router.get("/logs")
async def get_torob_logs(lines: int = 100):
    return await manager.get_logs("torob", lines)


@router.get("/exports")
async def list_torob_exports():
    return await manager.list_exports("torob")
