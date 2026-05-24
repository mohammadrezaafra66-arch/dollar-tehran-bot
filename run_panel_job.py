from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / 'data' / 'panel_worker_state.json'


if __name__ == '__main__':
    print({'state_file': str(STATE_PATH), 'exists': STATE_PATH.exists()})
