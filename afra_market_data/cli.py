from __future__ import annotations

import argparse
import json
import time

from .core import jalali_stamp, load_config, post_to_afra, run_once
from .source_check import check_sources, enable_successful_pending, save_report


def main():
    parser = argparse.ArgumentParser("afra-market-data")
    parser.add_argument("command", nargs="?", default="run-once", choices=["run-once", "run-loop", "post", "check-sources", "check-pending", "enable-pending"])
    parser.add_argument("--config", default="configs/indicators.json")
    parser.add_argument("--indicator", default=None)
    parser.add_argument("--source", default=None)
    parser.add_argument("--min-value", type=int, default=1)
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

    if args.command in ("check-sources", "check-pending"):
        rows = check_sources(
            config_path=args.config,
            include_disabled=True,
            indicator_code=args.indicator,
            source_code=args.source,
        )
        if args.command == "check-pending":
            rows = [row for row in rows if not row.get("enabled")]
        report_path = save_report(rows)
        ok_count = sum(1 for row in rows if row.get("ok"))
        bad_count = len(rows) - ok_count
        print(json.dumps({"checked": len(rows), "ok": ok_count, "bad": bad_count, "report": report_path}, ensure_ascii=False, indent=2))
        return

    if args.command == "enable-pending":
        result = enable_successful_pending(
            config_path=args.config,
            indicator_code=args.indicator,
            source_code=args.source,
            min_value=args.min_value,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
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
