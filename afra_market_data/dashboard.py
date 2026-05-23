from __future__ import annotations

import json
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse

from .core import changed_sources, jalali_stamp, live_payload, load_config, run_once

CONFIG = "configs/indicators.json"
BOTS_CONFIG = "configs/bots.json"
_stop = threading.Event()
_worker: threading.Thread | None = None
_state = {"running": False, "last_error": None, "last_run_at": None}


def _db_path() -> str:
    cfg = load_config(CONFIG)
    return cfg.get("app", {}).get("sqlite_path", "data/market_data.db")


def _load_bots_config() -> dict:
    path = Path(BOTS_CONFIG)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"portal": {"title": "مرکز مدیریت ربات‌های افرا کالا"}, "bots": []}


def _collector_loop() -> None:
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


app = FastAPI(title="Afra Local Bot Portal", lifespan=lifespan)


def _css() -> str:
    return """
    :root{--bg:#eef2f8;--card:#fff;--text:#101828;--muted:#667085;--line:#e5e7eb;--blue:#2563eb;--green:#16a34a;--orange:#d97706;--red:#dc2626;--dark:#0f172a;--shadow:0 18px 50px rgba(15,23,42,.10)}
    *{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top right,rgba(37,99,235,.18),transparent 35%),var(--bg);color:var(--text);font-family:Tahoma,Arial,sans-serif;line-height:1.7}.wrap{max-width:1450px;margin:auto;padding:22px}.hero{background:linear-gradient(135deg,#0f172a,#1d4ed8 55%,#0891b2);color:#fff;border-radius:30px;padding:26px;box-shadow:var(--shadow);margin-bottom:18px}.hero-row{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.title{font-size:30px;font-weight:900;margin:0 0 8px}.sub{color:#dbeafe;margin:0}.badge{display:inline-flex;gap:8px;align-items:center;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.24);border-radius:999px;padding:7px 12px;font-size:13px;margin-bottom:10px}.dot{width:9px;height:9px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 6px rgba(34,197,94,.15)}.actions{display:flex;gap:8px;flex-wrap:wrap}.btn{border:0;border-radius:14px;padding:10px 14px;font-weight:800;text-decoration:none;display:inline-flex;align-items:center;gap:8px;cursor:pointer;white-space:nowrap}.btn-primary{background:#fff;color:#0f172a}.btn-dark{background:#0f172a;color:#fff}.btn-soft{background:rgba(255,255,255,.14);color:#fff;border:1px solid rgba(255,255,255,.25)}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(285px,1fr));gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:22px;box-shadow:var(--shadow);padding:18px}.muted{color:var(--muted);font-size:13px}.pill{display:inline-flex;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:800}.pill.active{background:#dcfce7;color:#166534}.pill.planned{background:#fef3c7;color:#92400e}.pill.bad{background:#fee2e2;color:#991b1b}.bot-card{min-height:230px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden}.bot-card:before{content:"";position:absolute;inset:0 0 auto;height:5px;background:linear-gradient(90deg,#2563eb,#22c55e)}.bot-top{display:flex;gap:13px}.icon{width:54px;height:54px;border-radius:18px;background:#eef2ff;color:#1d4ed8;display:grid;place-items:center;font-weight:900}.bot-card h3{margin:0 0 4px;font-size:18px}.bot-actions{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:16px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}.stat b{font-size:28px}.toolbar{display:grid;grid-template-columns:1fr 230px;gap:10px;margin:16px 0}.control{width:100%;border:1px solid var(--line);border-radius:16px;padding:12px 14px;font-family:inherit}.panel-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:14px}.field{margin-bottom:10px}.field label{display:block;font-size:13px;color:var(--muted);margin-bottom:4px}.field input,.field select,.field textarea{width:100%;border:1px solid var(--line);border-radius:12px;padding:10px;font-family:inherit}.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:16px 0}.kpi b{font-size:26px}.table-wrap{max-height:520px;overflow:auto;border-radius:18px;border:1px solid var(--line)}table{width:100%;border-collapse:separate;border-spacing:0;background:#fff;font-size:13px}th,td{padding:10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}th{position:sticky;top:0;background:#f8fafc;color:var(--muted)}.ltr{direction:ltr;text-align:left;font-family:Consolas,monospace}.price{font-size:26px;font-weight:900;direction:ltr;text-align:left}.rate-card{border:1px solid var(--line);border-radius:18px;padding:14px;background:#fff}.empty{text-align:center;color:var(--muted);padding:22px}@media(max-width:900px){.hero-row,.panel-grid{display:block}.stats,.kpis,.toolbar{grid-template-columns:1fr}.actions{margin-top:14px}}
    """


def _layout(title: str, subtitle: str, body: str, actions: str = "") -> str:
    return f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title><style>{_css()}</style></head><body><div class="wrap"><header class="hero"><div class="hero-row"><div><div class="badge"><span class="dot"></span><span>Afra Local Bot Portal</span></div><h1 class="title">{title}</h1><p class="sub">{subtitle}</p></div><div class="actions"><a class="btn btn-soft" href="/">صفحه ربات‌ها</a>{actions}</div></div></header>{body}</div></body></html>"""


def portal_page() -> str:
    cfg = _load_bots_config()
    portal = cfg.get("portal", {})
    bots = sorted(cfg.get("bots", []), key=lambda x: int(x.get("order", 999)))
    total = len(bots)
    active = len([b for b in bots if b.get("status") == "active"])
    planned = len([b for b in bots if b.get("status") != "active"])
    cards = []
    for bot in bots:
        status = bot.get("status", "planned")
        cards.append(f"""
        <article class="card bot-card">
          <div><div class="bot-top"><div class="icon">{bot.get('icon','BOT')}</div><div><h3>{bot.get('name')}</h3><div class="muted">{bot.get('description','')}</div></div></div></div>
          <div class="bot-actions"><span class="pill {status}">{'فعال' if status == 'active' else 'در برنامه'}</span><a class="btn btn-dark" href="{bot.get('panel_url','#')}">ورود به پنل</a></div>
        </article>
        """)
    body = f"""
    <section class="stats"><div class="card stat"><div class="muted">کل ربات‌ها</div><b>{total}</b></div><div class="card stat"><div class="muted">فعال</div><b>{active}</b></div><div class="card stat"><div class="muted">در توسعه</div><b>{planned}</b></div><div class="card stat"><div class="muted">ظرفیت هدف</div><b>20+</b></div></section>
    <section class="grid">{''.join(cards)}</section>
    <section class="card" style="margin-top:16px"><h3>نحوه اضافه کردن ربات جدید</h3><p class="muted">برای ربات جدید فقط یک رکورد به <span class="ltr">configs/bots.json</span> اضافه می‌شود و برای آن مسیر پنل اختصاصی ساخته می‌شود. این ساختار برای حداقل ۲۰ ربات آماده است.</p></section>
    """
    return _layout(portal.get("title", "مرکز مدیریت ربات‌های افرا کالا"), portal.get("subtitle", "مدیریت ربات‌های محلی"), body, '<a class="btn btn-primary" href="/bots/market-data">ورود سریع به نرخ شاخص‌ها</a>')


def lead_panel_page(kind: str) -> str:
    is_maps = kind == "maps"
    title = "ربات استخراج لید از گوگل مپ" if is_maps else "ربات استخراج لید از دیوار"
    subtitle = "پنل اولیه تعریف سناریو، فیلترها و خروجی لیدها. منطق استخراج در مرحله بعد به این پنل وصل می‌شود."
    source_name = "Google Maps" if is_maps else "Divar"
    fields = """
      <div class="field"><label>شهر / منطقه هدف</label><input placeholder="مثلاً تهران، کرج، مشهد"></div>
      <div class="field"><label>کلمه کلیدی / صنف</label><input placeholder="مثلاً فروشگاه لوازم خانگی، کابینت، تعمیرکار"></div>
      <div class="field"><label>حداکثر تعداد لید</label><input type="number" value="100"></div>
    """
    if is_maps:
        fields += """
        <div class="field"><label>شعاع جستجو</label><select><option>۵ کیلومتر</option><option>۱۰ کیلومتر</option><option>کل شهر</option></select></div>
        <div class="field"><label>فیلدهای خروجی</label><textarea rows="3">نام کسب‌وکار، تلفن، آدرس، امتیاز، لینک گوگل مپ</textarea></div>
        """
    else:
        fields += """
        <div class="field"><label>دسته‌بندی دیوار</label><input placeholder="مثلاً خدمات، املاک، لوازم خانگی"></div>
        <div class="field"><label>فیلتر آگهی</label><textarea rows="3">عنوان، شهر، قیمت، شماره تماس در صورت مجاز، لینک آگهی</textarea></div>
        """
    body = f"""
    <section class="panel-grid">
      <div class="card"><h3>تعریف سناریوی استخراج</h3><p class="muted">این فرم فعلاً اسکلت مدیریتی است و برای اتصال موتور استخراج {source_name} آماده شده است.</p>{fields}<button class="btn btn-dark" onclick="alert('موتور استخراج هنوز به این پنل وصل نشده است')">ثبت سناریو</button></div>
      <div class="card"><h3>وضعیت ربات</h3><p><span class="pill planned">آماده اتصال موتور استخراج</span></p><p class="muted">در مرحله بعد باید ماژول استخراج، ذخیره‌سازی لیدها، جلوگیری از تکرار، خروجی Excel/CSV و API داخلی برای این ربات اضافه شود.</p><hr><h3>خروجی‌های هدف</h3><ul><li>نام لید / کسب‌وکار</li><li>شماره تماس در صورت مجاز بودن منبع</li><li>آدرس و شهر</li><li>لینک منبع</li><li>زمان استخراج و وضعیت اعتبارسنجی</li></ul></div>
    </section>
    <section class="card" style="margin-top:16px"><h3>آخرین لیدها</h3><div class="empty">هنوز داده‌ای استخراج نشده است.</div></section>
    """
    return _layout(title, subtitle, body)


def market_dashboard_page() -> str:
    body = """
    <div class="kpis" id="kpis"></div>
    <section class="card"><h3>کارت شاخص‌ها</h3><div class="grid" id="snapshotCards"></div></section>
    <section class="card" style="margin-top:16px"><h3>منابع و Observationهای اخیر</h3><div class="table-wrap"><table><thead><tr><th>شاخص</th><th>منبع</th><th>نوع</th><th>قیمت</th><th>وضعیت</th><th>تاخیر</th><th>زمان</th><th>خطا</th></tr></thead><tbody id="observations"></tbody></table></div></section>
    <script>
    let latestData={};function fmt(n){if(n===null||n===undefined||n==='')return '—';let x=Number(n);return Number.isFinite(x)?x.toLocaleString('en-US'):String(n)}function esc(s){return String(s??'').replace(/[&<>'\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]))}function parsePayload(r){try{return JSON.parse(r.payload_json||'{}')}catch(e){return {}}}function health(ok,total){if(!total)return 'bad';let r=ok/total;return r>=.75?'active':r>=.4?'planned':'bad'}
    function render(data){latestData=data;let snaps=data.snapshots||[],obs=data.recent_observations||[],ok=obs.filter(x=>x.ok===1).length,bad=obs.length-ok;document.getElementById('kpis').innerHTML=`<div class="card stat"><div class="muted">شاخص‌ها</div><b>${snaps.length}</b></div><div class="card stat"><div class="muted">منابع اخیر</div><b>${obs.length}</b></div><div class="card stat"><div class="muted">سالم</div><b>${ok}</b></div><div class="card stat"><div class="muted">خطادار</div><b>${bad}</b></div><div class="card stat"><div class="muted">زمان</div><b style="font-size:18px">${data.server_time?.iran_time_fa||'—'}</b></div>`;document.getElementById('snapshotCards').innerHTML=snaps.map(s=>`<div class="rate-card"><b>${esc(s.indicator_name)}</b><div class="price">${fmt(s.value_toman)}</div><span class="pill ${health(s.ok_count,s.source_count)}">${s.ok_count}/${s.source_count} منبع سالم</span><div class="muted ltr">${esc(s.indicator_code)}</div></div>`).join('')||'<div class="empty">هنوز snapshot ثبت نشده است.</div>';document.getElementById('observations').innerHTML=obs.map(r=>{let p=parsePayload(r);return `<tr><td>${esc(p.indicator_name||r.indicator_code)}</td><td>${esc(p.source_name||r.source_code)}</td><td>${esc(r.price_kind)}</td><td class="ltr">${fmt(r.value_toman)}</td><td>${r.ok===1?'<span class="pill active">سالم</span>':'<span class="pill bad">خطا</span>'}</td><td class="ltr">${r.latency_ms||'—'} ms</td><td>${esc(r.observed_at_jalali)} ${esc(r.observed_time_iran)}</td><td>${esc(r.error||'')}</td></tr>`}).join('')||'<tr><td colspan="8" class="empty">داده‌ای وجود ندارد.</td></tr>'}
    async function loadLive(){let r=await fetch('/api/live');render(await r.json())}function startStream(){let es=new EventSource('/api/stream');es.onmessage=e=>render(JSON.parse(e.data));es.onerror=()=>{es.close();setInterval(loadLive,5000)}}loadLive();startStream();
    </script>
    """
    actions = '<button class="btn btn-primary" onclick="fetch(\'/api/run-once\',{method:\'POST\'}).then(()=>location.reload())">اجرای فوری</button><a class="btn btn-soft" href="/api/live" target="_blank">JSON زنده</a>'
    return _layout("ربات استخراج نرخ شاخص‌ها از منابع", "داشبورد زنده نرخ ارز، طلا، سکه و شاخص‌های مالی", body, actions)


@app.get("/", response_class=HTMLResponse)
def home():
    return portal_page()


@app.get("/bots/market-data", response_class=HTMLResponse)
def market_data_panel():
    return market_dashboard_page()


@app.get("/bots/google-maps-leads", response_class=HTMLResponse)
def google_maps_leads_panel():
    return lead_panel_page("maps")


@app.get("/bots/divar-leads", response_class=HTMLResponse)
def divar_leads_panel():
    return lead_panel_page("divar")


@app.get("/dashboard")
def old_dashboard_redirect():
    return RedirectResponse(url="/bots/market-data")


@app.get("/api/bots")
def api_bots():
    return JSONResponse(_load_bots_config())


@app.get("/favicon.ico")
def favicon():
    svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='16' fill='#1d4ed8'/><path d='M16 42 28 20l7 13 5-9 8 18z' fill='white'/></svg>"
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/api/live")
def api_live():
    return JSONResponse(live_payload(_db_path()))


@app.get("/api/changed-sources")
def api_changed_sources(indicator_code: str = Query("usd_tehran"), updated_within_minutes: int = Query(15, ge=1, le=1440), compare_minutes: int = Query(20, ge=1, le=1440)):
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
