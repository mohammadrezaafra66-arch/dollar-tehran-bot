from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import divar, torob, google_maps


@asynccontextmanager
async def lifespan(app):
    (Path.cwd() / "data").mkdir(exist_ok=True)
    yield

app = FastAPI(title="G3 Bot Panel", version="1.0.0", lifespan=lifespan)

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
