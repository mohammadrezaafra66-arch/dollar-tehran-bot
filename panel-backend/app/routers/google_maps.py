from fastapi import APIRouter
from ..services.bot_manager import BotManager
from ..models.schemas import BotStartRequest

router = APIRouter(prefix="/api/google-maps", tags=["GoogleMaps"])
manager = BotManager()


@router.post("/start")
async def start_google_maps(params: BotStartRequest):
    return await manager.start_bot("google-maps", params.model_dump())


@router.post("/stop")
async def stop_google_maps():
    return await manager.stop_bot("google-maps")


@router.get("/status")
async def get_google_maps_status():
    return await manager.get_status("google-maps")


@router.get("/logs")
async def get_google_maps_logs(lines: int = 100):
    return await manager.get_logs("google-maps", lines)


@router.get("/exports")
async def list_google_maps_exports():
    return await manager.list_exports("google-maps")
