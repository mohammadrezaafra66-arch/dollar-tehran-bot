from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .config import load_config
from .scraper import DollarScraper
from .storage import Storage

app = FastAPI(title='Dollar Tehran Price Bot')
config = load_config()
storage = Storage(config['app']['sqlite_path'])


@app.get('/api/latest')
def latest():
    return storage.latest_prices(200)


@app.post('/api/run-once')
def run_once():
    scraper = DollarScraper(config, storage)
    rows = scraper.run_once()
    return {'count': len(rows), 'rows': rows}


@app.get('/api/logs')
def logs():
    return storage.logs(200)


@app.get('/', response_class=HTMLResponse)
def dashboard():
    rows = storage.latest_per_source()
    latest = storage.latest_prices(200)
    ok_rows = [r for r in rows if r.get('status') == 'success' and r.get('average_price_toman')]
    prices = [int(r['average_price_toman']) for r in ok_rows]
    avg = round(sum(prices) / len(prices)) if prices else None
    minp = min(prices) if prices else None
    maxp = max(prices) if prices else None
    diff = maxp - minp if minp and maxp else None

    def fmt(v):
        return f'{int(v):,}' if v is not None else '-'

    table_rows = ''.join(
        f'''
        <tr>
          <td>{r.get('source_name') or ''}</td>
          <td>{r.get('source_code') or ''}</td>
          <td>{fmt(r.get('buy_price_toman'))}</td>
          <td>{fmt(r.get('sell_price_toman'))}</td>
          <td>{fmt(r.get('average_price_toman'))}</td>
          <td>{r.get('status') or ''}</td>
          <td>{r.get('collected_at') or ''}</td>
          <td><a href="{r.get('source_url') or '#'}" target="_blank">منبع</a></td>
          <td>{r.get('error_message') or ''}</td>
        </tr>
        '''
        for r in rows
    )

    history_rows = ''.join(
        f'''
        <tr>
          <td>{r.get('collected_at') or ''}</td>
          <td>{r.get('source_name') or ''}</td>
          <td>{fmt(r.get('average_price_toman'))}</td>
          <td>{r.get('raw_price_text') or ''}</td>
          <td>{r.get('status') or ''}</td>
        </tr>
        '''
        for r in latest[:50]
    )

    return f'''
    <!doctype html>
    <html lang="fa" dir="rtl">
    <head>
      <meta charset="utf-8">
      <title>ربات قیمت دلار تهران</title>
      <style>
        body {{ font-family: Tahoma, Arial, sans-serif; background:#f6f7f9; margin: 24px; color:#222; }}
        .cards {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-bottom:18px; }}
        .card {{ background:white; border-radius:12px; padding:16px; box-shadow:0 1px 4px #ddd; }}
        .num {{ font-size:24px; font-weight:bold; margin-top:8px; }}
        table {{ width:100%; border-collapse:collapse; background:white; margin-bottom:24px; }}
        th, td {{ border-bottom:1px solid #eee; padding:10px; text-align:right; }}
        th {{ background:#f0f2f5; }}
        button {{ padding:10px 16px; border:0; border-radius:8px; cursor:pointer; }}
        .hint {{ background:#fff7dd; padding:12px; border-radius:10px; margin-bottom:16px; }}
      </style>
    </head>
    <body>
      <h1>ربات قیمت دلار تهران</h1>
      <div class="hint">این برنامه مستقل است و فقط در صورت فعال‌کردن sync، خروجی را به جدول پویا در دستیار افراکالا می‌فرستد.</div>
      <p><button onclick="runBot()">دریافت قیمت جدید</button></p>
      <div class="cards">
        <div class="card">میانگین منابع موفق<div class="num">{fmt(avg)}</div></div>
        <div class="card">کمترین قیمت<div class="num">{fmt(minp)}</div></div>
        <div class="card">بیشترین قیمت<div class="num">{fmt(maxp)}</div></div>
        <div class="card">اختلاف منابع<div class="num">{fmt(diff)}</div></div>
      </div>
      <h2>آخرین قیمت هر منبع</h2>
      <table>
        <tr><th>منبع</th><th>کد</th><th>خرید</th><th>فروش</th><th>میانگین/آخرین</th><th>وضعیت</th><th>زمان جمع‌آوری</th><th>لینک</th><th>خطا</th></tr>
        {table_rows}
      </table>
      <h2>تاریخچه اخیر</h2>
      <table>
        <tr><th>زمان</th><th>منبع</th><th>قیمت</th><th>متن خام</th><th>وضعیت</th></tr>
        {history_rows}
      </table>
      <script>
        async function runBot() {{
          const res = await fetch('/api/run-once', {{method:'POST'}});
          const data = await res.json();
          alert('انجام شد: ' + data.count + ' منبع');
          location.reload();
        }}
      </script>
    </body>
    </html>
    '''
