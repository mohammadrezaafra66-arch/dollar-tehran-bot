from fastapi import APIRouter, HTTPException
from ..services.bot_manager import BotManager
from ..models.schemas import BotStartRequest

router = APIRouter(prefix="/api/divar", tags=["Divar"])
manager = BotManager()


@router.post("/start")
async def start_divar(params: BotStartRequest):
    return await manager.start_bot("divar", params.model_dump())


@router.post("/stop")
async def stop_divar():
    return await manager.stop_bot("divar")


@router.get("/status")
async def get_divar_status():
    return await manager.get_status("divar")


@router.get("/logs")
async def get_divar_logs(lines: int = 100):
    return await manager.get_logs("divar", lines)


@router.get("/exports")
async def list_divar_exports():
    return await manager.list_exports("divar")
