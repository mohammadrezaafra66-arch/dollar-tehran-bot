from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
QUEUE_PATH = DATA_DIR / 'panel_job_requests.jsonl'
STATE_PATH = DATA_DIR / 'panel_worker_state.json'
MAPS_RUN = BASE_DIR / 'google-maps-bot' / 'run.py'


def queue_exists() -> bool:
    return QUEUE_PATH.exists()


def read_queue() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    items = []
    with QUEUE_PATH.open('r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def write_state(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open('w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def target_for(item: dict) -> str:
    if item.get('bot_id') == 'google_maps_leads':
        return str(MAPS_RUN)
    return ''


def summary() -> dict:
    jobs = read_queue()
    return {'queue_exists': queue_exists(), 'count': len(jobs), 'targets': [target_for(job) for job in jobs]}


if __name__ == '__main__':
    data = summary()
    write_state(data)
    print(data)
