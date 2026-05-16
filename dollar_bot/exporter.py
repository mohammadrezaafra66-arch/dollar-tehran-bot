from __future__ import annotations

from pathlib import Path

import pandas as pd

from .storage import Storage
from .utils import now_iso


def export_latest(storage: Storage, export_dir: str, tz: str = 'Asia/Tehran') -> dict[str, str]:
    rows = storage.latest_prices(10000)
    logs = storage.logs(1000)
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    stamp = now_iso(tz).replace(':', '-')
    xlsx = Path(export_dir) / f'dollar_prices_{stamp}.xlsx'
    csv = Path(export_dir) / f'dollar_prices_{stamp}.csv'
    df = pd.DataFrame(rows)
    df.to_csv(csv, index=False, encoding='utf-8-sig')
    with pd.ExcelWriter(xlsx, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dollar_Prices')
        pd.DataFrame(logs).to_excel(writer, index=False, sheet_name='Logs')
    return {'xlsx': str(xlsx), 'csv': str(csv)}
