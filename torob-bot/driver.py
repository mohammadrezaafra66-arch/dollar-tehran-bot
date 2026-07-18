import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone Torob bot")
    parser.add_argument("--mode", choices=["run", "status", "sync"], required=True)
    parser.add_argument("--query", default="اسپیکر بلوتوث")
    args = parser.parse_args()

    orchestrator = Orchestrator()

    if args.mode == "status":
        print(json.dumps(orchestrator.status(), ensure_ascii=False, indent=2))
        return

    if args.mode == "sync":
        print(json.dumps(orchestrator.sync_pending(), ensure_ascii=False, indent=2))
        return

    async def _run() -> None:
        result = await orchestrator.run(args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    asyncio.run(_run())


if __name__ == "__main__":
    main()
