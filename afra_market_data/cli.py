from __future__ import annotations

import argparse
import json
import time

from .core import jalali_stamp, load_config, post_to_afra, run_once


def main():
    parser = argparse.ArgumentParser("afra-market-data")
    parser.add_argument("command", nargs="?", default="run-once", choices=["run-once", "run-loop", "post"])
    parser.add_argument("--config", default="configs/indicators.json")
    args = parser.parse_args()

    if args.command == "run-once":
        payload = run_once(args.config)
        print(json.dumps(payload["meta"], ensure_ascii=False, indent=2))
        return

    if args.command == "post":
        cfg = load_config(args.config)
        payload = run_once(args.config)
        ok, msg = post_to_afra(payload, cfg)
        print(("OK: " if ok else "ERROR: ") + msg)
        return

    cfg = load_config(args.config)
    interval = int(cfg.get("collector", {}).get("dashboard_poll_interval_seconds", 15))
    while True:
        started = jalali_stamp()
        print(f"[{started['jalali_date']} {started['iran_time']}] collecting market data...")
        try:
            payload = run_once(args.config)
            print(f"done. snapshots={len(payload.get('snapshots', []))} sources={payload.get('meta', {}).get('source_count')}")
        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")
        print(f"next run in {interval} seconds")
        time.sleep(interval)


if __name__ == "__main__":
    main()
