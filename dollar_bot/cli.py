from __future__ import annotations

import argparse
import time
from uuid import uuid4

from .afrakala_sync import AfraKalaSync
from .config import load_config
from .exporter import export_latest
from .scraper import DollarScraper
from .storage import Storage


def _fmt_price(value):
    if value is None:
        return '-'
    try:
        return f'{int(value):,}'
    except Exception:
        return str(value)


def _print_rows(rows: list[dict]) -> None:
    print('')
    print('Source results:')
    print('-' * 80)
    for row in rows:
        name = row.get('source_name') or row.get('source_code') or '-'
        code = row.get('source_code') or '-'
        status = row.get('status') or '-'
        price = _fmt_price(row.get('average_price_toman'))
        error = row.get('error_message') or ''
        raw = row.get('raw_price_text') or ''
        print(f'{code} | {name} | {status} | price={price}')
        if raw:
            print(f'  raw: {raw[:160]}')
        if error:
            print(f'  error: {error[:300]}')
    print('-' * 80)
    print('')


def run_once(config_path: str | None = None, sync: bool = True, export: bool = False) -> None:
    config = load_config(config_path)
    storage = Storage(config['app']['sqlite_path'])
    scraper = DollarScraper(config, storage)
    job_id = 'JOB-' + uuid4().hex[:12].upper()
    rows = scraper.run_once(job_id=job_id)
    ok = sum(1 for r in rows if r.get('status') == 'success')
    fail = len(rows) - ok
    print(f'Job: {job_id}')
    print(f'Collected: {len(rows)} | success={ok} | failed={fail}')
    _print_rows(rows)

    if sync:
        try:
            AfraKalaSync(config).push_rows(rows)
            if config.get('sync', {}).get('enabled'):
                print('Synced to AfraKala dynamic table.')
        except Exception as exc:
            storage.log('error', f'AfraKala sync failed: {exc}', job_id=job_id)
            print(f'AfraKala sync failed: {exc}')

    if export:
        paths = export_latest(storage, config['app']['export_dir'], config['app'].get('timezone', 'Asia/Tehran'))
        print(f'Exported: {paths}')


def run_loop(config_path: str | None = None) -> None:
    config = load_config(config_path)
    interval = int(config.get('schedule', {}).get('interval_minutes', 15))
    while True:
        run_once(config_path=config_path, sync=True, export=False)
        print(f'Sleeping {interval} minutes...')
        time.sleep(interval * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description='Dollar Tehran Price Bot')
    parser.add_argument('command', choices=['run-once', 'run-loop', 'export'])
    parser.add_argument('--config', default=None)
    parser.add_argument('--no-sync', action='store_true')
    args = parser.parse_args()

    if args.command == 'run-once':
        run_once(config_path=args.config, sync=not args.no_sync)
    elif args.command == 'run-loop':
        run_loop(config_path=args.config)
    elif args.command == 'export':
        config = load_config(args.config)
        storage = Storage(config['app']['sqlite_path'])
        paths = export_latest(storage, config['app']['export_dir'], config['app'].get('timezone', 'Asia/Tehran'))
        print(paths)


if __name__ == '__main__':
    main()
