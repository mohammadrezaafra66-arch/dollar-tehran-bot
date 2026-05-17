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


def badge_status(value):
    v = str(value or '').lower()
    label = esc(value or '-')
    if v in ('success', 'healthy'):
        return f'<span class="badge green">● {label}</span>'
    if v == 'cooldown':
        return f'<span class="badge amber">● {label}</span>'
    if v in ('failed', 'error'):
        return f'<span class="badge red">● {label}</span>'
    return f'<span class="badge gray">● {label}</span>'


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
    healthy_count = len([h for h in health_rows if h.get('status') == 'healthy'])
    last_time = latest[0].get('collected_at') if latest else '-'
    system_state = 'سالم' if error_count == 0 and cooldown_count == 0 else 'نیازمند بررسی'

    table_rows = ''.join(
        f'''
        <tr class="{'ok' if r.get('status') == 'success' else 'bad'}">
          <td><strong>{esc(r.get('source_name'))}</strong><small>{esc(r.get('source_code'))}</small></td>
          <td class="money">{fmt(r.get('average_price_toman'))}</td>
          <td>{badge_status(r.get('status'))}</td>
          <td>{esc(r.get('collected_at'))}</td>
          <td><a class="link" href="{esc(r.get('source_url') or '#')}" target="_blank">باز کردن منبع</a></td>
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
          <td class="money smallmoney">{fmt(r.get('average_price_toman'))}</td>
          <td><code>{esc(r.get('raw_price_text'))}</code></td>
          <td>{badge_status(r.get('status'))}</td>
          <td class="err">{esc(r.get('error_message'))}</td>
        </tr>
        '''
        for r in latest[:80]
    )

    now_epoch = int(time.time())
    health_html = ''.join(
        f'''
        <tr class="{'ok' if h.get('status') == 'healthy' else 'warn' if h.get('status') == 'cooldown' else 'bad'}">
          <td><strong>{esc(h.get('source_name'))}</strong><small>{esc(h.get('source_code'))}</small></td>
          <td>{badge_status(h.get('status'))}</td>
          <td>{esc(h.get('consecutive_failures'))}</td>
          <td>{esc(h.get('total_success'))}</td>
          <td>{esc(h.get('total_failed'))}</td>
          <td>{esc(h.get('last_success_at'))}</td>
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
          <td>{badge_status(l.get('level'))}</td>
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
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>مانیتورینگ ربات شاخص‌های بازار</title>
      <style>
        :root {{
          --bg:#0f172a; --panel:#111827; --panel2:#182235; --card:#ffffff; --text:#0f172a;
          --muted:#64748b; --line:#e5e7eb; --green:#16a34a; --red:#dc2626; --amber:#d97706; --blue:#2563eb;
        }}
        * {{ box-sizing:border-box; }}
        body {{ margin:0; font-family: Tahoma, Arial, sans-serif; background:#f4f7fb; color:var(--text); }}
        .hero {{ background:linear-gradient(135deg,#0f172a,#1e3a8a 55%,#0891b2); color:white; padding:26px 28px 34px; border-bottom-left-radius:28px; border-bottom-right-radius:28px; box-shadow:0 18px 45px rgba(15,23,42,.25); }}
        .topbar {{ display:flex; justify-content:space-between; align-items:center; gap:16px; }}
        .title h1 {{ margin:0; font-size:30px; letter-spacing:-.5px; }}
        .title p {{ margin:10px 0 0; color:#dbeafe; }}
        .actions {{ display:flex; gap:10px; align-items:center; }}
        button {{ border:0; border-radius:14px; padding:12px 18px; cursor:pointer; color:white; font-weight:700; background:linear-gradient(135deg,#22c55e,#16a34a); box-shadow:0 10px 22px rgba(22,163,74,.28); }}
        .ghost {{ background:rgba(255,255,255,.14); box-shadow:none; border:1px solid rgba(255,255,255,.25); }}
        .status-pill {{ padding:10px 14px; border-radius:999px; background:rgba(255,255,255,.14); border:1px solid rgba(255,255,255,.22); font-size:13px; }}
        .wrap {{ padding:0 22px 28px; max-width:1800px; margin:-22px auto 0; }}
        .cards {{ display:grid; grid-template-columns: repeat(7, minmax(150px,1fr)); gap:14px; margin-bottom:18px; }}
        .card {{ background:white; border-radius:20px; padding:16px; box-shadow:0 12px 30px rgba(15,23,42,.08); border:1px solid rgba(226,232,240,.9); min-height:108px; }}
        .card .label {{ color:var(--muted); font-size:12px; }}
        .card .num {{ font-size:26px; font-weight:900; margin-top:12px; direction:ltr; text-align:right; }}
        .card.green {{ border-top:4px solid var(--green); }} .card.red {{ border-top:4px solid var(--red); }} .card.amber {{ border-top:4px solid var(--amber); }} .card.blue {{ border-top:4px solid var(--blue); }}
        .grid {{ display:grid; grid-template-columns: 1.15fr .85fr; gap:18px; }}
        .section {{ background:white; border-radius:22px; padding:18px; box-shadow:0 12px 30px rgba(15,23,42,.07); border:1px solid #e8edf4; margin-bottom:18px; overflow:hidden; }}
        .section h2 {{ margin:0 0 14px; display:flex; align-items:center; gap:10px; font-size:20px; }}
        .section h2:before {{ content:''; width:9px; height:28px; border-radius:20px; background:linear-gradient(#2563eb,#06b6d4); display:inline-block; }}
        .tablebox {{ overflow:auto; max-height:520px; border-radius:16px; border:1px solid #edf2f7; }}
        table {{ width:100%; border-collapse:separate; border-spacing:0; background:white; font-size:13px; }}
        th, td {{ border-bottom:1px solid #edf2f7; padding:12px 11px; text-align:right; vertical-align:top; white-space:nowrap; }}
        th {{ background:#f8fafc; color:#334155; position:sticky; top:0; z-index:1; font-size:12px; }}
        tr:hover td {{ background:#f8fbff; }}
        tr.ok td {{ border-right:3px solid #22c55e; }} tr.bad td {{ border-right:3px solid #ef4444; }} tr.warn td {{ border-right:3px solid #f59e0b; }}
        small {{ display:block; color:var(--muted); margin-top:5px; direction:ltr; text-align:right; }}
        .money {{ font-size:20px; font-weight:900; direction:ltr; color:#0f172a; }} .smallmoney {{ font-size:15px; }}
        .badge {{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:6px 10px; font-size:12px; font-weight:700; }}
        .badge.green {{ background:#dcfce7; color:#166534; }} .badge.red {{ background:#fee2e2; color:#991b1b; }} .badge.amber {{ background:#fef3c7; color:#92400e; }} .badge.gray {{ background:#e5e7eb; color:#374151; }}
        .err {{ color:#b91c1c; max-width:480px; white-space:normal; word-break:break-word; }}
        .link {{ color:#2563eb; text-decoration:none; font-weight:700; }}
        code {{ direction:ltr; display:block; white-space:pre-wrap; text-align:left; max-width:540px; color:#334155; background:#f8fafc; border-radius:10px; padding:8px; }}
        .hint {{ background:#eff6ff; color:#1e3a8a; padding:13px 15px; border-radius:16px; margin-bottom:16px; border:1px solid #bfdbfe; }}
        @media (max-width:1200px) {{ .cards {{ grid-template-columns: repeat(2,1fr); }} .grid {{ grid-template-columns:1fr; }} .topbar {{ flex-direction:column; align-items:flex-start; }} }}
      </style>
    </head>
    <body>
      <div class="hero">
        <div class="topbar">
          <div class="title">
            <h1>مانیتورینگ ربات شاخص‌های بازار</h1>
            <p>پایش قیمت‌ها، سلامت منابع، خطاها، cooldown و وضعیت احتمالی بلاک شدن در یک داشبورد واحد</p>
          </div>
          <div class="actions">
            <span class="status-pill">وضعیت کلی: <strong>{system_state}</strong></span>
            <button onclick="runBot()">دریافت قیمت جدید</button>
            <button class="ghost" onclick="location.reload()">Refresh داشبورد</button>
          </div>
        </div>
      </div>
      <div class="wrap">
        <div class="cards">
          <div class="card blue"><div class="label">آخرین بروزرسانی</div><div class="num" style="font-size:16px;direction:rtl">{esc(last_time)}</div></div>
          <div class="card green"><div class="label">منابع سالم</div><div class="num">{healthy_count}</div></div>
          <div class="card red"><div class="label">منابع خطادار</div><div class="num">{error_count}</div></div>
          <div class="card amber"><div class="label">در cooldown</div><div class="num">{cooldown_count}</div></div>
          <div class="card"><div class="label">میانگین منابع موفق</div><div class="num">{fmt(avg)}</div></div>
          <div class="card"><div class="label">کمترین قیمت</div><div class="num">{fmt(minp)}</div></div>
          <div class="card"><div class="label">بیشترین قیمت</div><div class="num">{fmt(maxp)}</div></div>
        </div>
        <div class="hint">Refresh صفحه فقط داده‌های ذخیره‌شده را نشان می‌دهد و به سایت‌ها درخواست جدید نمی‌زند. برای جمع‌آوری تازه، دکمه «دریافت قیمت جدید» یا فایل run_loop.bat را اجرا کن.</div>

        <div class="grid">
          <div class="section">
            <h2>آخرین قیمت هر شاخص</h2>
            <div class="tablebox"><table>
              <tr><th>شاخص</th><th>قیمت تومان</th><th>وضعیت</th><th>زمان جمع‌آوری</th><th>لینک</th><th>خطا</th></tr>
              {table_rows}
            </table></div>
          </div>
          <div class="section">
            <h2>سلامت منابع</h2>
            <div class="tablebox"><table>
              <tr><th>منبع</th><th>وضعیت</th><th>خطای پیاپی</th><th>موفق</th><th>خطا</th><th>آخرین موفق</th><th>نوع خطا</th><th>HTTP</th><th>ms</th><th>cooldown</th><th>پیام</th></tr>
              {health_html}
            </table></div>
          </div>
        </div>

        <div class="section">
          <h2>تاریخچه اخیر</h2>
          <div class="tablebox"><table>
            <tr><th>زمان</th><th>شاخص</th><th>قیمت</th><th>متن خام</th><th>وضعیت</th><th>خطا</th></tr>
            {history_rows}
          </table></div>
        </div>

        <div class="section">
          <h2>لاگ کامل خطاها و رویدادها</h2>
          <div class="tablebox"><table>
            <tr><th>زمان سیستم</th><th>سطح</th><th>منبع</th><th>پیام</th><th>جزئیات فنی</th></tr>
            {logs_html}
          </table></div>
        </div>
      </div>
      <script>
        async function runBot() {{
          const btn = event.target;
          btn.disabled = true;
          btn.innerText = 'در حال دریافت...';
          try {{
            const res = await fetch('/api/run-once', {{method:'POST'}});
            const data = await res.json();
            alert('انجام شد: ' + data.count + ' شاخص');
            location.reload();
          }} catch(e) {{
            alert('خطا در اجرای ربات: ' + e);
            btn.disabled = false;
            btn.innerText = 'دریافت قیمت جدید';
          }}
        }}
      </script>
    </body>
    </html>
    '''
