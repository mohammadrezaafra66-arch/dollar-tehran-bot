from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
PANEL_DIR = BASE_DIR / "panel"
CONFIG_PATH = BASE_DIR / "configs" / "bots.json"

app = FastAPI(title="Afra Local Bot Control Center")

app.mount("/static", StaticFiles(directory=str(PANEL_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(PANEL_DIR / "templates"))


def load_portal_config() -> dict:
    if not CONFIG_PATH.exists():
        return {
            "portal": {
                "title": "Afra Local Bot Control Center",
                "subtitle": "Local control panel for Afra automation bots",
                "version": "0.1.0",
            },
            "bots": [],
        }

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    config = load_portal_config()
    bots = sorted(config.get("bots", []), key=lambda bot: bot.get("order", 999))

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "portal": config.get("portal", {}),
            "bots": bots,
        },
    )
