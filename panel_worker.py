from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUEUE_PATH = BASE_DIR / 'data' / 'panel_job_requests.jsonl'


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


if __name__ == '__main__':
    print({'queue_exists': queue_exists(), 'jobs': read_queue()})
