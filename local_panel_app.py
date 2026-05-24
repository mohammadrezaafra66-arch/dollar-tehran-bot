from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'configs' / 'bots.json'
GOOGLE_MAPS_RUNNER = BASE_DIR / 'google-maps-bot' / 'run.py'
JOB_QUEUE_PATH = BASE_DIR / 'data' / 'panel_job_requests.jsonl'
INPUT_SETTINGS_PATH = BASE_DIR / 'data' / 'panel_google_maps_inputs.json'
MANAGE_SETTINGS_PATH = BASE_DIR / 'data' / 'panel_google_maps_manage.json'
OUTPUTS_PATH = BASE_DIR / 'data' / 'panel_outputs_registry.json'

app = FastAPI(title='Afra Local Panel')


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


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/bots')
def bots():
    config = load_portal_config()
    return {'bots': config.get('bots', [])}


@app.get('/api/google-maps/runner-exists')
def google_maps_runner_exists():
    return {'exists': GOOGLE_MAPS_RUNNER.exists()}


@app.post('/api/google-maps/request-run')
def request_google_maps_run():
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


@app.get('/api/google-maps/manage')
def get_google_maps_manage():
    return read_json(MANAGE_SETTINGS_PATH, {'execution_window': {'start': '00:00', 'end': '23:59'}, 'limits': {'max_queries': 10, 'max_businesses_per_query': 50}, 'delays': {'between_queries': '20-60', 'between_clicks': '5-15'}, 'status': 'pause'})


@app.get('/api/google-maps/outputs')
def get_google_maps_outputs():
    return read_json(OUTPUTS_PATH, {'items': []})


@app.post('/api/google-maps/inputs/sample')
def create_sample_google_maps_input():
    data = {'items': [{'province': 'تهران', 'city': 'تهران', 'keyword': 'فروشگاه لوازم خانگی', 'brand': '', 'related_keywords': '', 'category': 'لوازم خانگی', 'active': True}]}
    write_json(INPUT_SETTINGS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/manage/sample')
def create_sample_google_maps_manage():
    data = {'execution_window': {'start': '00:00', 'end': '23:59'}, 'limits': {'max_queries': 10, 'max_businesses_per_query': 50}, 'delays': {'between_queries': '20-60', 'between_clicks': '5-15'}, 'status': 'resume'}
    write_json(MANAGE_SETTINGS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/outputs/sample')
def create_sample_output_registry():
    data = {'items': [{'file_name': 'google_maps_results.xlsx', 'records': 120, 'status': 'ready'}]}
    write_json(OUTPUTS_PATH, data)
    return {'saved': True, 'data': data}
