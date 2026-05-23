# run.py
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.config import Config
from app.main_orchestrator import main

if __name__ == "__main__":
    # بررسی مجوز اجرا
    if not Config.is_execution_allowed():
        print("⏸️ Execution not allowed. Exiting.")
        sys.exit(0)
    
    main()