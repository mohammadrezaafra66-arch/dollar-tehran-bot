# run.py
import os
import sys

# Ensure project root is importable when running: python run.py
sys.path.insert(0, os.path.dirname(__file__))

from app.main_orchestrator import Orchestrator


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
