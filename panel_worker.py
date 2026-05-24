from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUEUE_PATH = BASE_DIR / 'data' / 'panel_job_requests.jsonl'


def queue_exists() -> bool:
    return QUEUE_PATH.exists()


if __name__ == '__main__':
    print({'queue_exists': queue_exists(), 'queue': str(QUEUE_PATH)})
