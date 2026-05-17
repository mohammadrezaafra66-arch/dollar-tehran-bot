from __future__ import annotations

import html
import json
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .config import load_config
from .scraper import DollarScraper
from .storage import Storage

app = FastAPI(title='Market Indicators Bot')
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


@app.get('/api/health')
def health():
    return storage.source_health()


def esc(v):
    return html.escape(str(v or ''))


def fmt(v):
    try:
        return f'{int(v):,}' if v is not None and v != '' else '-'
    except Exception:
        return '-'


def parse_details(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except Exception:
        return {}


@app.get('/', response_class=HTMLResponse)
def dashboard():
    rows = storage.latest_per_source()
    latest = storage.latest_prices(200)
    health_rows = storage.source_health()
    logs = storage.logs(100)

    ok_rows = [r for r in rows if r.get('status') == 'success' and r.get('average_price_toman')]
    prices = [int(r['average_price_toman']) for r in ok_rows]
    avg = round(sum(prices) / len(prices)) if prices else None
    minp = min(prices) if prices else None
    maxp = max(prices) if prices else None
    diff = maxp - minp if minp and maxp else None
    error_count = len([r for r in rows if r.get('status') != 'success'])
    cooldown_count = len([h for h in health_rows if h.get('status') == 'cooldown'])

    table_rows = ''.join(
        f'''
        <tr class="{'ok' if r.get('status') == 'success' else 'bad'}">
          <td>{esc(r.get('source_name'))}</td>
          <td>{esc(r.get('source_code'))}</td>
          <td>{fmt(r.get('buy_price_toman'))}</td>
          <td>{fmt(r.get('sell_price_toman'))}</td>
          <td>{fmt(r.get('average_price_toman'))}</td>
          <td>{esc(r.get('status'))}</td>
          <td>{esc(r.get('collected_at'))}</td>
          <td><a href="{esc(r.get('source_url') or '#')}" target="_blank">منبع</a></td>
          <td class="err">{esc(r.get('error_message'))}</td>
        </tr>
        '''
        for r in rows
    )

    history_rows = ''.join(
        f'''
        <tr class="{'ok' if r.get('status') == 'success' else 'bad'}">
          <td>{esc(r.get('collected_at'))}</td>
          <td>{esc(r.get('source_name'))}</td>
          <td>{fmt(r.get('average_price_toman'))}</td>
          <td>{esc(r.get('raw_price_text'))}</td>
          <td>{esc(r.get('status'))}</td>
          <td class="err">{esc(r.get('error_message'))}</td>
        </tr>
        '''
        for r in latest[:80]
    )

    now_epoch = int(time.time())
    health_html = ''.join(
        f'''
        <tr class="{'ok' if h.get('status') == 'healthy' else 'warn' if h.get('status') == 'cooldown' else 'bad'}">
          <td>{esc(h.get('source_name'))}</td>
          <td>{esc(h.get('source_code'))}</td>
          <td>{esc(h.get('status'))}</td>
          <td>{esc(h.get('consecutive_failures'))}</td>
          <td>{esc(h.get('total_success'))}</td>
          <td>{esc(h.get('total_failed'))}</td>
          <td>{esc(h.get('last_success_at'))}</td>
          <td>{esc(h.get('last_failed_at'))}</td>
          <td>{esc(h.get('last_error_type'))}</td>
          <td>{esc(h.get('last_http_status'))}</td>
          <td>{esc(h.get('last_response_ms'))}</td>
          <td>{max(0, int(h.get('cooldown_until_epoch') or 0) - now_epoch)}</td>
          <td class="err">{esc(h.get('last_error_message'))}</td>
        </tr>
        '''
        for h in health_rows
    )

    logs_html = ''.join(
        f'''
        <tr class="{'bad' if l.get('level') in ('error','critical') else 'warn' if l.get('level') == 'warning' else ''}">
          <td>{esc(l.get('created_at'))}</td>
          <td>{esc(l.get('level'))}</td>
          <td>{esc(l.get('source_code'))}</td>
          <td>{esc(l.get('message'))}</td>
          <td><code>{esc(l.get('details_json'))}</code></td>
        </tr>
        '''
        for l in logs[:80]
    )

    return f'''
    <!doctype html>
    <html lang="fa" dir="rtl">
    <head>
      <meta charset="utf-8">
      <title>داشبورد ربات شاخص‌های بازار</title>
      <style>
        body {{ font-family: Tahoma, Arial, sans-serif; background:#f6f7f9; margin: 22px; color:#222; }}
        h1 {{ margin-bottom: 8px; }}
        h2 {{ margin-top: 28px; }}
        .cards {{ display:grid; grid-template-columns: repeat(6, 1fr); gap:12px; margin:18px 0; }}
        .card {{ background:white; border-radius:12px; padding:14px; box-shadow:0 1px 4px #ddd; }}
        .num {{ font-size:24px; font-weight:bold; margin-top:8px; }}
        table {{ width:100%; border-collapse:collapse; background:white; margin-bottom:24px; font-size:13px; }}
        th, td {{ border-bottom:1px solid #eee; padding:9px; text-align:right; vertical-align:top; }}
        th {{ background:#f0f2f5; position: sticky; top: 0; }}
        button {{ padding:10px 16px; border:0; border-radius:8px; cursor:pointer; background:#1976d2; color:white; }}
        .hint {{ background:#fff7dd; padding:12px; border-radius:10px; margin-bottom:16px; }}
        .ok td {{ background:#f5fff5; }}
        .bad td {{ background:#fff3f3; }}
        .warn td {{ background:#fffbe8; }}
        .err {{ color:#a40000; max-width:420px; word-break:break-word; }}
        code {{ direction:ltr; display:block; white-space:pre-wrap; text-align:left; max-width:520px; }}
      </style>
    </head>
    <body>
      <h1>داشبورد ربات شاخص‌های بازار</h1>
      <div class="hint">ربات با محدودیت درخواست، ثبت خطا، تشخیص timeout/403/429، شمارش خطاهای پشت‌سرهم و cooldown منبع کار می‌کند. Refresh داشبورد درخواست جدید به سایت نمی‌زند؛ فقط دکمه زیر یا run_loop قیمت جدید می‌گیرد.</div>
      <p><button onclick="runBot()">دریافت قیمت جدید</button></p>
      <div class="cards">
        <div class="card">میانگین منابع موفق<div class="num">{fmt(avg)}</div></div>
        <div class="card">کمترین قیمت<div class="num">{fmt(minp)}</div></div>
        <div class="card">بیشترین قیمت<div class="num">{fmt(maxp)}</div></div>
        <div class="card">اختلاف منابع<div class="num">{fmt(diff)}</div></div>
        <div class="card">منابع خطادار<div class="num">{error_count}</div></div>
        <div class="card">در cooldown<div class="num">{cooldown_count}</div></div>
      </div>

      <h2>آخرین قیمت هر شاخص</h2>
      <table>
        <tr><th>منبع</th><th>کد</th><th>خرید</th><th>فروش</th><th>میانگین/آخرین</th><th>وضعیت</th><th>زمان جمع‌آوری</th><th>لینک</th><th>خطا</th></tr>
        {table_rows}
      </table>

      <h2>سلامت منابع و وضعیت بلاک/خطا</h2>
      <table>
        <tr><th>منبع</th><th>کد</th><th>وضعیت سلامت</th><th>خطای پشت‌سرهم</th><th>موفق کل</th><th>خطای کل</th><th>آخرین موفق</th><th>آخرین خطا</th><th>نوع خطا</th><th>HTTP</th><th>زمان پاسخ ms</th><th>مانده cooldown ثانیه</th><th>پیام خطا</th></tr>
        {health_html}
      </table>

      <h2>تاریخچه اخیر</h2>
      <table>
        <tr><th>زمان</th><th>منبع</th><th>قیمت</th><th>متن خام</th><th>وضعیت</th><th>خطا</th></tr>
        {history_rows}
      </table>

      <h2>لاگ کامل خطاها و رویدادها</h2>
      <table>
        <tr><th>زمان سیستم</th><th>سطح</th><th>منبع</th><th>پیام</th><th>جزئیات فنی</th></tr>
        {logs_html}
      </table>

      <script>
        async function runBot() {{
          const res = await fetch('/api/run-once', {{method:'POST'}});
          const data = await res.json();
          alert('انجام شد: ' + data.count + ' شاخص');
          location.reload();
        }}
      </script>
    </body>
    </html>
    '''
