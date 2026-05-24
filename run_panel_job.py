from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
STATE_PATH = DATA_DIR / 'panel_worker_state.json'
LOG_DIR = DATA_DIR / 'panel_runtime_logs'
MAPS_DIR = BASE_DIR / 'google-maps-bot'
MAPS_RUN = MAPS_DIR / 'run.py'


def now() -> str:
    return datetime.now().isoformat(timespec='seconds')


def write_state(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def read_state() -> dict:
    if not STATE_PATH.exists():
        return {'status': 'missing_state'}
    return json.loads(STATE_PATH.read_text(encoding='utf-8'))


def run_job() -> dict:
    state = read_state()
    if state.get('status') not in {'ready_to_run', 'requested'}:
        return {'status': 'skipped', 'reason': 'state_not_ready', 'state': state}
    if not MAPS_RUN.exists():
        result = {'status': 'failed', 'reason': 'missing_runner', 'runner': str(MAPS_RUN), 'finished_at': now()}
        write_state(result)
        return result
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f'run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    running = {'status': 'running', 'runner': str(MAPS_RUN), 'started_at': now(), 'log_path': str(log_path)}
    write_state(running)
    completed = subprocess.run([sys.executable, str(MAPS_RUN)], cwd=str(MAPS_DIR), capture_output=True, text=True)
    log_path.write_text((completed.stdout or '') + '\n\n--- STDERR ---\n' + (completed.stderr or ''), encoding='utf-8')
    result = {'status': 'completed' if completed.returncode == 0 else 'failed', 'returncode': completed.returncode, 'finished_at': now(), 'log_path': str(log_path)}
    write_state(result)
    return result


if __name__ == '__main__':
    print(run_job())
