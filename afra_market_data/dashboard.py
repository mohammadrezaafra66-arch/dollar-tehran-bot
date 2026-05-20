from __future__ import annotations

import json
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from .core import changed_sources, jalali_stamp, live_payload, load_config, run_once

CONFIG = "configs/indicators.json"
_state = {"running": False, "last_error": None, "last_run_at": None}
_stop = threading.Event()
_worker: threading.Thread | None = None


def _db_path() -> str:
    cfg = load_config(CONFIG)
    return cfg.get("app", {}).get("sqlite_path", "data/market_data.db")


def _collector_loop():
    cfg = load_config(CONFIG)
    interval = int(cfg.get("collector", {}).get("dashboard_poll_interval_seconds", 15))
    _state["running"] = True
    while not _stop.is_set():
        try:
            run_once(CONFIG)
            _state["last_error"] = None
            _state["last_run_at"] = jalali_stamp()
        except Exception as exc:
            _state["last_error"] = f"{type(exc).__name__}: {exc}"
        _stop.wait(interval)
    _state["running"] = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _worker
    _stop.clear()
    _worker = threading.Thread(target=_collector_loop, name="afra-market-collector", daemon=True)
    _worker.start()
    yield
    _stop.set()


app = FastAPI(title="Afra Market Data Dashboard", lifespan=lifespan)


def html_page() -> str:
    return """<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>داشبورد زنده شاخص‌های افرا کالا</title>
  <style>
    body{font-family:tahoma,Arial;background:#f3f4f6;margin:0;color:#111827} .wrap{max-width:1380px;margin:24px auto;padding:0 16px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card{background:white;border-radius:18px;padding:16px;box-shadow:0 8px 28px #00000010;margin-bottom:14px}
    .kpi{font-size:26px;font-weight:800;margin-top:8px}.muted{color:#667085;font-size:13px}.ok{color:#067647}.bad{color:#b42318}.warn{color:#b54708}
    button,.btn{border:0;background:#111827;color:white;padding:10px 14px;border-radius:10px;text-decoration:none;margin:3px;cursor:pointer}button.secondary{background:#475467}
    table{width:100%;border-collapse:collapse;background:white;font-size:13px}td,th{padding:10px;border-bottom:1px solid #eee;text-align:right;vertical-align:top}th{background:#f8fafc;position:sticky;top:0}.pill{padding:3px 8px;border-radius:999px;background:#eef2ff;display:inline-block}.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.ltr{direction:ltr;text-align:left}
  </style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h2>داشبورد زنده شاخص‌های بازار افرا کالا</h2>
    <p class="muted">برای ۵۰ شاخص × ۵ منبع طراحی شده؛ داده‌ها بدون refresh صفحه به‌روزرسانی می‌شوند.</p>
    <div class="toolbar"><button onclick="runNow()">اجرای فوری</button><button class="secondary" onclick="loadLive()">دریافت دستی آخرین وضعیت</button><a class="btn" href="/api/live" target="_blank">JSON زنده</a><span id="serverTime" class="muted"></span><span id="status" class="muted"></span></div>
  </div>
  <div class="grid" id="kpis"></div>
  <div class="card"><h3>Snapshot زنده شاخص‌ها</h3><table><thead><tr><th>شاخص</th><th>قیمت نهایی</th><th>منابع سالم</th><th>روش</th><th>زمان ایران</th></tr></thead><tbody id="snapshots"></tbody></table></div>
  <div class="card"><h3>آخرین Observationها</h3><table><thead><tr><th>شاخص</th><th>منبع</th><th>نوع</th><th>قیمت تومان</th><th>کیفیت</th><th>تاخیر</th><th>وضعیت</th><th>خطا</th><th>زمان</th></tr></thead><tbody id="observations"></tbody></table></div>
</div>
<script>
function fmt(n){ if(n===null || n===undefined) return '-'; return Number(n).toLocaleString('en-US'); }
function esc(s){return String(s ?? '').replace(/[&<>'"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function render(data){
  const time=data.server_time||{}; document.getElementById('serverTime').innerText='آخرین دریافت: '+(time.jalali_date_fa||'')+' '+(time.iran_time_fa||'');
  const snaps=data.snapshots||[]; const obs=data.recent_observations||[];
  document.getElementById('kpis').innerHTML = `<div class="card"><div class="muted">تعداد شاخص</div><div class="kpi">${snaps.length}</div></div><div class="card"><div class="muted">آخرین observationها</div><div class="kpi">${obs.length}</div></div><div class="card"><div class="muted">منابع سالم آخرین اجرا</div><div class="kpi">${obs.filter(x=>x.ok===1).length}</div></div><div class="card"><div class="muted">خطادار</div><div class="kpi bad">${obs.filter(x=>x.ok!==1).length}</div></div>`;
  document.getElementById('snapshots').innerHTML = snaps.map(s=>`<tr><td>${esc(s.indicator_name)}</td><td class="ltr">${fmt(s.value_toman)}</td><td>${s.ok_count}/${s.source_count}</td><td><span class="pill">${esc(s.method)}</span></td><td>${esc(s.created_at_jalali)} ${esc(s.created_time_iran)}</td></tr>`).join('');
  document.getElementById('observations').innerHTML = obs.map(r=>{let p={}; try{p=JSON.parse(r.payload_json||'{}')}catch(e){}; return `<tr><td>${esc(p.indicator_name||r.indicator_code)}</td><td>${esc(p.source_name||r.source_code)}</td><td>${esc(r.price_kind)}</td><td class="ltr">${fmt(r.value_toman)}</td><td>${r.quality_score}</td><td>${r.latency_ms||'-'} ms</td><td>${r.ok===1?'<span class="ok">سالم</span>':'<span class="bad">خطا</span>'}</td><td>${esc(r.error||'')}</td><td>${esc(r.observed_at_jalali)} ${esc(r.observed_time_iran)}</td></tr>`}).join('');
}
async function loadLive(){ const r=await fetch('/api/live'); render(await r.json()); }
async function runNow(){ document.getElementById('status').innerText='در حال اجرای فوری...'; const r=await fetch('/api/run-once',{method:'POST'}); const j=await r.json(); document.getElementById('status').innerText='نتیجه: '+j.status; await loadLive(); }
function startStream(){ const es=new EventSource('/api/stream'); es.onmessage=(ev)=>{render(JSON.parse(ev.data));}; es.onerror=()=>{document.getElementById('status').innerText='اتصال زنده قطع شد؛ polling فعال است'; setInterval(loadLive,5000); es.close();}; }
loadLive(); startStream();
</script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return html_page()


@app.get("/api/live")
def api_live():
    return JSONResponse(live_payload(_db_path()))


@app.get("/api/changed-sources")
def api_changed_sources(
    indicator_code: str = Query("usd_tehran"),
    updated_within_minutes: int = Query(15, ge=1, le=1440),
    compare_minutes: int = Query(20, ge=1, le=1440),
):
    return JSONResponse(changed_sources(indicator_code, updated_within_minutes, compare_minutes, _db_path()))


@app.post("/api/run-once")
def api_run_once():
    try:
        payload = run_once(CONFIG)
        return {"status": "ok", "snapshots": len(payload.get("snapshots", []))}
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


@app.get("/api/stream")
def api_stream():
    def events():
        cfg = load_config(CONFIG)
        refresh = int(cfg.get("dashboard", {}).get("stream_refresh_seconds", 3))
        while True:
            yield "data: " + json.dumps(live_payload(_db_path()), ensure_ascii=False) + "\n\n"
            time.sleep(refresh)
    return StreamingResponse(events(), media_type="text/event-stream")
