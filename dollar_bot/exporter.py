from __future__ import annotations

import csv
from pathlib import Path

from .storage import Storage
from .utils import now_iso


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text('', encoding='utf-8-sig')
        return
    fieldnames = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_latest(storage: Storage, export_dir: str, tz: str = 'Asia/Tehran') -> dict[str, str]:
    rows = storage.latest_prices(10000)
    logs = storage.logs(1000)
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    stamp = now_iso(tz).replace(':', '-').replace('+', '_')
    prices_csv = Path(export_dir) / f'dollar_prices_{stamp}.csv'
    logs_csv = Path(export_dir) / f'dollar_logs_{stamp}.csv'
    _write_csv(prices_csv, rows)
    _write_csv(logs_csv, logs)
    return {'prices_csv': str(prices_csv), 'logs_csv': str(logs_csv)}
