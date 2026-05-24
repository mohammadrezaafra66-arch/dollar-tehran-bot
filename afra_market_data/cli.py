from __future__ import annotations

import argparse
import asyncio
import json
import time

from .core import jalali_stamp, load_config, post_to_afra, run_once
from .source_check import check_sources, enable_successful_pending, save_report
from .drivers.torob_driver import TorobDriver
from .core.logger import PlatformLogger
from .core.queue_manager import QueueManager, QueueJob
from .core.checkpoint_engine import CheckpointEngine
from .db.storage import SQLiteStorage
from .runtime.worker import WorkerRuntime
from .runtime.scheduler import SchedulerEngine


async def run_torob_dry():
    driver = TorobDriver()

    await driver.start()

    result = await driver.process(
        {
            'query': 'تلویزیون سامسونگ'
        }
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    await driver.stop()


def run_architecture_smoke_test():
    logger = PlatformLogger()
    queue = QueueManager()
    checkpoint = CheckpointEngine('data/checkpoints/smoke-test.json')
    storage = SQLiteStorage()
    scheduler = SchedulerEngine(interval_seconds=60)
    worker = WorkerRuntime(worker_name='smoke-test-worker', queue_manager=queue)

    queue.add_job(QueueJob(platform='torob', query='smoke test'))
    checkpoint.save({'status': 'ok', 'stage': 'architecture_smoke_test'})

    result = {
        'status': 'success',
        'logger': logger.__class__.__name__,
        'queue_size': queue.size(),
        'checkpoint_loaded': checkpoint.load(),
        'storage': storage.__class__.__name__,
        'scheduler': scheduler.__class__.__name__,
        'worker': worker.__class__.__name__,
    }

    checkpoint.clear()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser("afra-market-data")
    parser.add_argument(
        "command",
        nargs="?",
        default="run-once",
        choices=[
            "run-once",
            "run-loop",
            "post",
            "check-sources",
            "check-pending",
            "enable-pending",
            "torob-dry-run",
            "architecture-smoke-test"
        ]
    )
    parser.add_argument("--config", default="configs/indicators.json")
    parser.add_argument("--indicator", default=None)
    parser.add_argument("--source", default=None)
    parser.add_argument("--min-value", type=int, default=1)
    args = parser.parse_args()

    if args.command == "architecture-smoke-test":
        run_architecture_smoke_test()
        return

    if args.command == "torob-dry-run":
        asyncio.run(run_torob_dry())
        return

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
