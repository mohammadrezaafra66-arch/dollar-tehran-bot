from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'configs' / 'bots.json'
GOOGLE_MAPS_RUNNER = BASE_DIR / 'google-maps-bot' / 'run.py'
GOOGLE_MAPS_OUTPUT_DIR = BASE_DIR / 'google-maps-bot' / 'output'
GOOGLE_MAPS_LOG_DIR = BASE_DIR / 'google-maps-bot' / 'logs'
JOB_QUEUE_PATH = BASE_DIR / 'data' / 'panel_job_requests.jsonl'
INPUT_SETTINGS_PATH = BASE_DIR / 'data' / 'panel_google_maps_inputs.json'
MANAGE_SETTINGS_PATH = BASE_DIR / 'data' / 'panel_google_maps_manage.json'
OUTPUTS_PATH = BASE_DIR / 'data' / 'panel_outputs_registry.json'
LOGS_PATH = BASE_DIR / 'data' / 'panel_logs_registry.json'
WORKER_STATE_PATH = BASE_DIR / 'data' / 'panel_worker_state.json'
UI_PATH = BASE_DIR / 'panel_ui.html'
ADMIN_PASSWORD = os.getenv('AFRA_PANEL_ADMIN_PASSWORD', '')

app = FastAPI(title='Afra Local Panel')


def auth_enabled() -> bool:
    return bool(ADMIN_PASSWORD)


def require_admin(x_panel_password: str | None = Header(default=None)) -> None:
    if ADMIN_PASSWORD and x_panel_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail='unauthorized')


def load_portal_config() -> dict:
    if not CONFIG_PATH.exists():
        return {'portal': {'title': 'Afra Local Panel'}, 'bots': []}
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        return json.load(file)


def read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open('r', encoding='utf-8') as file:
        return json.load(file)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def list_files(folder: Path) -> list[dict]:
    if not folder.exists():
        return []
    items = []
    for path in sorted(folder.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.is_file():
            items.append({'name': path.name, 'path': str(path), 'size': path.stat().st_size})
    return items


def safe_output_file(file_name: str) -> Path:
    path = (GOOGLE_MAPS_OUTPUT_DIR / file_name).resolve()
    if GOOGLE_MAPS_OUTPUT_DIR.resolve() not in path.parents or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail='file not found')
    return path


def path_status(path: Path) -> dict:
    return {'path': str(path), 'exists': path.exists()}


@app.get('/', response_class=HTMLResponse)
def home():
    if UI_PATH.exists():
        return UI_PATH.read_text(encoding='utf-8')
    return '<h1>Afra Local Panel</h1><p>Use /docs for API testing.</p>'


@app.get('/api/health')
def health():
    return {'status': 'ok', 'paths': {'runner': path_status(GOOGLE_MAPS_RUNNER), 'output_dir': path_status(GOOGLE_MAPS_OUTPUT_DIR), 'log_dir': path_status(GOOGLE_MAPS_LOG_DIR), 'ui': path_status(UI_PATH)}}


@app.get('/api/auth-mode')
def panel_auth_mode():
    return {'auth_enabled': auth_enabled()}


@app.get('/api/bots')
def bots():
    config = load_portal_config()
    return {'bots': config.get('bots', [])}


@app.get('/api/google-maps/worker-state')
def google_maps_worker_state():
    return read_json(WORKER_STATE_PATH, {'status': 'unknown'})


@app.get('/api/google-maps/runner-exists')
def google_maps_runner_exists():
    return {'exists': GOOGLE_MAPS_RUNNER.exists()}


@app.post('/api/google-maps/request-run')
def request_google_maps_run(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    JOB_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    item = {'bot_id': 'google_maps_leads', 'status': 'requested'}
    with JOB_QUEUE_PATH.open('a', encoding='utf-8') as file:
        file.write(json.dumps(item, ensure_ascii=False) + '\n')
    return {'accepted': True, 'queue': str(JOB_QUEUE_PATH)}


@app.get('/api/google-maps/queue')
def google_maps_queue():
    if not JOB_QUEUE_PATH.exists():
        return {'jobs': [], 'total': 0}
    jobs = []
    with JOB_QUEUE_PATH.open('r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                jobs.append(json.loads(line))
    return {'jobs': jobs, 'total': len(jobs)}


@app.get('/api/google-maps/inputs')
def get_google_maps_inputs():
    return read_json(INPUT_SETTINGS_PATH, {'items': []})


@app.post('/api/google-maps/inputs/save')
def save_google_maps_inputs(data: dict, x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    items = data.get('items')
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail='items must be a list')
    write_json(INPUT_SETTINGS_PATH, {'items': items})
    return {'saved': True, 'total': len(items), 'data': {'items': items}}


@app.get('/api/google-maps/manage')
def get_google_maps_manage():
    return read_json(MANAGE_SETTINGS_PATH, {'execution_window': {'start': '00:00', 'end': '23:59'}, 'limits': {'max_queries': 10, 'max_businesses_per_query': 50}, 'delays': {'between_queries': '20-60', 'between_clicks': '5-15'}, 'status': 'pause'})


@app.get('/api/google-maps/outputs')
def get_google_maps_outputs():
    registry = read_json(OUTPUTS_PATH, {'items': []})
    return {'items': registry.get('items', []), 'files': list_files(GOOGLE_MAPS_OUTPUT_DIR)}


@app.get('/api/google-maps/logs')
def get_google_maps_logs():
    registry = read_json(LOGS_PATH, {'items': []})
    return {'items': registry.get('items', []), 'files': list_files(GOOGLE_MAPS_LOG_DIR)}


@app.get('/api/google-maps/downloads')
def get_google_maps_downloads():
    return {'items': list_files(GOOGLE_MAPS_OUTPUT_DIR)}


@app.get('/api/google-maps/download/{file_name}')
def download_google_maps_output(file_name: str):
    path = safe_output_file(file_name)
    return FileResponse(str(path), filename=path.name)


@app.post('/api/google-maps/inputs/sample')
def create_sample_google_maps_input(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'items': [{'province': 'تهران', 'city': 'تهران', 'keyword': 'فروشگاه لوازم خانگی', 'brand': '', 'related_keywords': '', 'category': 'لوازم خانگی', 'active': True}]}
    write_json(INPUT_SETTINGS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/manage/sample')
def create_sample_google_maps_manage(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'execution_window': {'start': '00:00', 'end': '23:59'}, 'limits': {'max_queries': 10, 'max_businesses_per_query': 50}, 'delays': {'between_queries': '20-60', 'between_clicks': '5-15'}, 'status': 'resume'}
    write_json(MANAGE_SETTINGS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/outputs/sample')
def create_sample_output_registry(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'items': [{'file_name': 'google_maps_results.xlsx', 'records': 120, 'status': 'ready'}]}
    write_json(OUTPUTS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/logs/sample')
def create_sample_logs_registry(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'items': [{'level': 'INFO', 'message': 'Google Maps panel log registry initialized'}]}
    write_json(LOGS_PATH, data)
    return {'saved': True, 'data': data}
