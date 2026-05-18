from __future__ import annotations
import html, json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from .core import run_once, latest_rows, load_config, jalali_stamp, fa_num

app=FastAPI(title='Afra Market Data Dashboard')
CONFIG='configs/indicators.json'

def page(rows):
    stamp=jalali_stamp(); trs=[]
    for r in rows:
        payload=json.loads(r['payload']) if r.get('payload') else {}
        val='-' if r['value_toman'] is None else f"{int(r['value_toman']):,}"
        status='✅ سالم' if r['ok'] else '❌ خطا'
        trs.append(f"<tr><td>{html.escape(payload.get('indicator_name',''))}</td><td>{html.escape(payload.get('source_name',''))}</td><td>{html.escape(payload.get('price_kind',''))}</td><td>{val}</td><td>{status}</td><td>{html.escape(r.get('error') or '')}</td><td>{html.escape(payload.get('collected_at_jalali',''))} {html.escape(payload.get('collected_time_iran',''))}</td></tr>")
    return f'''<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>داشبورد افرا مارکت دیتا</title>
<style>body{{font-family:tahoma,Arial;background:#f6f7fb;margin:0;color:#222}}.wrap{{max-width:1200px;margin:30px auto;padding:0 16px}}.card{{background:white;border-radius:16px;padding:18px;margin-bottom:16px;box-shadow:0 6px 22px #0001}}button,a.btn{{border:0;background:#111827;color:white;padding:10px 16px;border-radius:10px;text-decoration:none;margin:4px;cursor:pointer}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{padding:10px;border-bottom:1px solid #eee;text-align:right}}th{{background:#f1f5f9}}.muted{{color:#667085}}</style></head><body><div class="wrap"><div class="card"><h2>داشبورد استخراج شاخص‌های افرا کالا</h2><p class="muted">تاریخ شمسی: {stamp['jalali_date_fa']} - ساعت ایران: {stamp['iran_time_fa']}</p><button onclick="runNow()">اجرای فوری ربات</button><a class="btn" href="/api/latest">خروجی JSON</a><a class="btn" href="/">رفرش داشبورد</a><p id="msg"></p></div><div class="card"><h3>آخرین استخراج‌ها</h3><table><thead><tr><th>شاخص</th><th>منبع</th><th>نوع قیمت</th><th>قیمت تومان</th><th>وضعیت</th><th>خطا</th><th>زمان ایران</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div></div><script>async function runNow(){{document.getElementById('msg').innerText='در حال اجرا...';let r=await fetch('/api/run-once',{{method:'POST'}});let j=await r.json();document.getElementById('msg').innerText='تمام شد: '+j.status;setTimeout(()=>location.reload(),800)}}</script></body></html>'''

@app.get('/', response_class=HTMLResponse)
def home():
    cfg=load_config(CONFIG); return page(latest_rows(cfg.get('app',{}).get('sqlite_path','data/market_data.db')))

@app.post('/api/run-once')
def api_run_once():
    p=run_once(CONFIG); return {'status':'ok','snapshots':len(p['snapshots'])}

@app.get('/api/latest')
def api_latest():
    cfg=load_config(CONFIG); return JSONResponse(latest_rows(cfg.get('app',{}).get('sqlite_path','data/market_data.db')))
