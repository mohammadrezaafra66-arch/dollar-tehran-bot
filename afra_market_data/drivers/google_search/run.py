import os, sys
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)
from app.main_orchestrator import Orchestrator

if __name__ == "__main__":
    for d in ['input','output','data','data/checkpoints','logs','screenshots']:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
    Orchestrator().run()
