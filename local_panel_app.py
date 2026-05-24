from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'configs' / 'bots.json'

app = FastAPI(title='Afra Local Panel')


def load_portal_config() -> dict:
    if not CONFIG_PATH.exists():
        return {'portal': {'title': 'Afra Local Panel'}, 'bots': []}
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        return json.load(file)


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/bots')
def bots():
    config = load_portal_config()
    return {'bots': config.get('bots', [])}
