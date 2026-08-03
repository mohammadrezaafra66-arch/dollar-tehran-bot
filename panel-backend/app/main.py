from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import divar, torob, google_maps
from .services.bot_manager import BotManager

app = FastAPI(title="G3 Bot Panel", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(divar.router)
app.include_router(torob.router)
app.include_router(google_maps.router)


@app.get("/api/health")
async def health():
    return {"status": "healthy", "bots": ["divar", "torob", "google-maps"]}


@app.get("/api/all-status")
async def all_status():
    manager = BotManager()
    statuses = {}
    for bot in ["divar", "torob", "google-maps"]:
        statuses[bot] = await manager.get_status(bot)
    return statuses
