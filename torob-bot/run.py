"""
Simple runner shortcut.
Usage: python run.py "اسپیکر بلوتوث"
"""
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(__file__))
from app.orchestrator import TorobOrchestrator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("استفاده: python run.py 'کلمه جستجو'")
        sys.exit(1)
    query = " ".join(sys.argv[1:])
    result = asyncio.run(TorobOrchestrator().run(query))
    print(json.dumps(result, ensure_ascii=False, indent=2))
