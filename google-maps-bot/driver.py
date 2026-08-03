#!/usr/bin/env python3
"""
Google Maps Bot — Driver wrapper for the unified panel-backend.
This matches the interface of divar-bot/driver.py and torob-bot/driver.py
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.main_orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(description="Run Google Maps bot")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file (JSON or YAML)",
        default=os.getenv("GOOGLE_MAPS_CONFIG_PATH", "config.yaml"),
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to input Excel file with search keywords",
        default=os.getenv("GOOGLE_MAPS_INPUT_PATH", "input/keywords.xlsx"),
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to output Excel file",
        default=os.getenv("GOOGLE_MAPS_OUTPUT_PATH", "output/results.xlsx"),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint",
    )

    args = parser.parse_args()

    orchestrator = Orchestrator()
    if args.resume:
        orchestrator.load_checkpoint()
    orchestrator.run()


if __name__ == "__main__":
    main()
