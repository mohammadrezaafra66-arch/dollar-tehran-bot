# run.py
import os
import sys

# Ensure project root is importable when running: python run.py
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)

from app.local_io import sync_local_settings_to_bot_inputs
from app.main_orchestrator import Orchestrator


def bootstrap_local_environment():
    """Prepare fully-local execution environment before bot startup."""
    required_dirs = [
        'input',
        'output',
        'data',
        'data/checkpoints',
        'logs',
        'screenshots',
        'database',
    ]

    for rel_dir in required_dirs:
        os.makedirs(os.path.join(BASE_DIR, rel_dir), exist_ok=True)

    sync_local_settings_to_bot_inputs()


if __name__ == "__main__":
    bootstrap_local_environment()

    print("=" * 60)
    print("📦 Local execution mode enabled")
    print(f"📁 Project root: {BASE_DIR}")
    print(f"📥 Local settings: {os.path.join(BASE_DIR, 'local_settings.xlsx')}")
    print(f"📤 Outputs: {os.path.join(BASE_DIR, 'output')}")
    print(f"🗄️ Database: {os.path.join(BASE_DIR, 'data', 'google_maps.db')}")
    print("=" * 60)

    orchestrator = Orchestrator()
    orchestrator.run()
