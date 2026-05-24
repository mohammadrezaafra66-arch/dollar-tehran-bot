from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUEUE_PATH = BASE_DIR / 'data' / 'panel_job_requests.jsonl'
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


def target_for(item: dict) -> str:
    if item.get('bot_id') == 'google_maps_leads':
        return str(MAPS_RUN)
    return ''


def summary() -> dict:
    jobs = read_queue()
    return {'queue_exists': queue_exists(), 'count': len(jobs), 'targets': [target_for(job) for job in jobs]}


if __name__ == '__main__':
    print(summary())
