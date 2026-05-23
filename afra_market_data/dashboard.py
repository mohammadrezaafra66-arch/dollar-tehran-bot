from __future__ import annotations

import json
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse, StreamingResponse

from .core import changed_sources, jalali_stamp, live_payload, load_config, run_once

CONFIG = "configs/indicators.json"
BOTS_CONFIG = "configs/bots.json"
_state = {"running": False, "last_error": None, "last_run_at": None}
_stop = threading.Event()
_worker: threading.Thread | None = None


def _db_path() -> str:
    cfg = load_config(CONFIG)
    return cfg.get("app", {}).get("sqlite_path", "data/market_data.db")


def _load_bots_config() -> dict:
    path = Path(BOTS_CONFIG)
    if not path.exists():
        return {
            "portal": {
                "title": "مرکز مدیریت ربات‌های افرا کالا",
                "subtitle": "داشبورد محلی مدیریت ربات‌ها",
                "version": "1.0.0",
            },
            "bots": [
                {
                    "id": "market_data",
                    "name": "ربات شاخص‌های بازار",
                    "short_name": "شاخص‌های بازار",
                    "description": "داشبورد زنده نرخ ارز، طلا و شاخص‌های مالی.",
                    "category": "market-intelligence",
                    "status": "active",
                    "panel_url": "/bots/market-data",
                    "api_url": "/api/live",
                    "icon": "📈",
                    "accent": "blue",
                    "order": 10,
                }
            ],
        }
    return json.loads(path.read_text(encoding="utf-8"))


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


app = FastAPI(title="Afra Local Bot Portal", lifespan=lifespan)


def base_css() -> str:
    return """
    :root{--bg:#eef2f8;--surface:#ffffff;--surface2:#f8fafc;--text:#101828;--muted:#667085;--line:#e4e7ec;--brand:#0f172a;--brand2:#2563eb;--accent:#16a34a;--danger:#dc2626;--warn:#d97706;--shadow:0 18px 50px rgba(15,23,42,.10);--radius:22px;--mono:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace}
    [data-theme="dark"]{--bg:#07111f;--surface:#0f172a;--surface2:#111c2f;--text:#e5e7eb;--muted:#94a3b8;--line:#263447;--brand:#e5e7eb;--brand2:#60a5fa;--shadow:0 18px 55px rgba(0,0,0,.35)}
    *{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top right,rgba(37,99,235,.18),transparent 34%),var(--bg);color:var(--text);font-family:Tahoma,Arial,sans-serif;line-height:1.65}.wrap{max-width:1500px;margin:0 auto;padding:22px}.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}.muted{color:var(--muted);font-size:13px}.btn{border:0;border-radius:14px;padding:10px 14px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:8px;transition:.18s;white-space:nowrap}.btn:hover{transform:translateY(-1px)}.pill{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:4px 9px;font-size:12px;background:#eef2ff;color:#3730a3}.pill.ok{background:#dcfce7;color:#166534}.pill.bad{background:#fee2e2;color:#991b1b}.pill.warn{background:#fef3c7;color:#92400e}.pill.planned{background:#f3f4f6;color:#475467}.control{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:12px 14px;color:var(--text);box-shadow:0 8px 24px rgba(15,23,42,.05);font-family:inherit}.ltr{direction:ltr;text-align:left;font-family:var(--mono)}
    .hero{position:relative;overflow:hidden;background:linear-gradient(135deg,#0f172a,#1d4ed8 55%,#0891b2);color:white;border-radius:30px;padding:24px;box-shadow:var(--shadow);margin-bottom:18px}.hero:after{content:"";position:absolute;inset:auto -80px -120px auto;width:360px;height:360px;background:rgba(255,255,255,.12);border-radius:50%}.hero-top{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;position:relative;z-index:1}.title{font-size:30px;font-weight:900;margin:0 0 6px}.subtitle{margin:0;color:#dbeafe}.badge{display:inline-flex;gap:7px;align-items:center;padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);font-size:13px}.dot{width:9px;height:9px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 6px rgba(34,197,94,.15)}.hero-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.btn-primary{background:white;color:#0f172a}.btn-ghost{background:rgba(255,255,255,.13);color:white;border:1px solid rgba(255,255,255,.25)}.theme-btn{background:var(--surface);color:var(--text);border:1px solid var(--line)}
    @media(max-width:1000px){.hero-top{flex-direction:column}.hero-actions{justify-content:flex-start}.title{font-size:24px}}@media(max-width:560px){.wrap{padding:12px}}
    """


def portal_page() -> str:
    cfg = _load_bots_config()
    portal = cfg.get("portal", {})
    bots = sorted(cfg.get("bots", []), key=lambda x: int(x.get("order", 999)))
    bots_json = json.dumps(bots, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{portal.get('title','مرکز مدیریت ربات‌های افرا کالا')}</title>
  <style>{base_css()}
    .portal-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:16px}}.bot-card{{padding:18px;position:relative;overflow:hidden;background:linear-gradient(180deg,var(--surface),var(--surface2));min-height:210px;display:flex;flex-direction:column;justify-content:space-between}}.bot-card:before{{content:"";position:absolute;inset:0 0 auto 0;height:5px;background:linear-gradient(90deg,#2563eb,#22c55e)}}.bot-top{{display:flex;gap:12px;align-items:flex-start}}.icon{{width:52px;height:52px;border-radius:18px;background:#eef2ff;display:grid;place-items:center;font-size:26px;flex:0 0 auto}}.bot-card h3{{margin:0 0 4px;font-size:18px}}.bot-actions{{display:flex;gap:8px;align-items:center;justify-content:space-between;margin-top:14px}}.open-btn{{background:#0f172a;color:white}}[data-theme="dark"] .open-btn{{background:#e5e7eb;color:#0f172a}}.disabled{{opacity:.62}}.disabled .open-btn{{pointer-events:none;background:#94a3b8;color:white}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}}.stat{{padding:14px}}.stat b{{font-size:24px}}.toolbar{{display:grid;grid-template-columns:1fr 220px auto;gap:10px;margin:18px 0}}.guide{{padding:18px;margin-top:16px}}.guide code{{background:var(--surface2);border:1px solid var(--line);border-radius:8px;padding:2px 6px;direction:ltr;display:inline-block}}@media(max-width:800px){{.toolbar,.stats{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="hero-top"><div><div class="badge"><span class="dot"></span><span>Local Bot Portal</span></div><h1 class="title">{portal.get('title','مرکز مدیریت ربات‌های افرا کالا')}</h1><p class="subtitle">{portal.get('subtitle','صفحه ورود محلی برای مدیریت ربات‌ها')}</p></div><div class="hero-actions"><a class="btn btn-primary" href="/bots/market-data">ورود به ربات شاخص‌ها</a><button class="btn btn-ghost" onclick="toggleTheme()">تغییر تم</button><a class="btn btn-ghost" href="/api/bots" target="_blank">Bot Registry JSON</a></div></div>
  </header>
  <div class="stats"><div class="card stat"><div class="muted">کل ربات‌های ثبت‌شده</div><b id="totalBots">—</b></div><div class="card stat"><div class="muted">فعال</div><b id="activeBots">—</b></div><div class="card stat"><div class="muted">آماده توسعه</div><b id="plannedBots">—</b></div><div class="card stat"><div class="muted">ظرفیت هدف</div><b>20+</b></div></div>
  <div class="toolbar"><input id="searchBox" class="control" placeholder="جستجو در ربات‌ها..." oninput="renderBots()"><select id="statusFilter" class="control" onchange="renderBots()"><option value="all">همه وضعیت‌ها</option><option value="active">فعال</option><option value="planned">در برنامه</option><option value="maintenance">نگهداری</option></select><button class="btn theme-btn" onclick="renderBots()">اعمال فیلتر</button></div>
  <main class="portal-grid" id="botsGrid"></main>
  <section class="card guide"><h3>معماری جدید</h3><p class="muted">برای اضافه کردن ربات جدید، یک رکورد به <code>configs/bots.json</code> اضافه کن و مسیر پنل آن را مشخص کن. صفحه اول به‌صورت خودکار کارت/دکمه ربات را می‌سازد. مسیر فعلی ربات شاخص‌های بازار: <code>/bots/market-data</code></p></section>
</div>
<script>
const bots={bots_json};
function esc(s){{return String(s??'').replace(/[&<>'"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}}[c]))}}
function statusLabel(s){{return s==='active'?'فعال':s==='planned'?'در برنامه':s==='maintenance'?'نگهداری':s}}
function renderStats(){{document.getElementById('totalBots').innerText=bots.length;document.getElementById('activeBots').innerText=bots.filter(b=>b.status==='active').length;document.getElementById('plannedBots').innerText=bots.filter(b=>b.status==='planned').length}}
function renderBots(){{const q=document.getElementById('searchBox').value.trim().toLowerCase();const st=document.getElementById('statusFilter').value;const list=bots.filter(b=>{{const hay=[b.name,b.short_name,b.description,b.category,b.status].join(' ').toLowerCase();return (!q||hay.includes(q))&&(st==='all'||b.status===st)}});document.getElementById('botsGrid').innerHTML=list.length?list.map(b=>{{const active=b.status==='active'&&b.panel_url&&b.panel_url!=='#';return `<article class="card bot-card ${{active?'':'disabled'}}"><div><div class="bot-top"><div class="icon">${{esc(b.icon||'🤖')}}</div><div><h3>${{esc(b.name)}}</h3><div class="muted">${{esc(b.description)}}</div></div></div></div><div class="bot-actions"><span class="pill ${{b.status==='active'?'ok':b.status==='planned'?'planned':'warn'}}">${{esc(statusLabel(b.status))}}</span><a class="btn open-btn" href="${{active?esc(b.panel_url):'#'}}">ورود به پنل</a></div></article>`}}).join(''):`<div class="card guide">رباتی با این فیلتر پیدا نشد.</div>`}}
function toggleTheme(){{const root=document.documentElement;const next=root.getAttribute('data-theme')==='dark'?'light':'dark';root.setAttribute('data-theme',next);localStorage.setItem('afraPortalTheme',next)}}
document.documentElement.setAttribute('data-theme',localStorage.getItem('afraPortalTheme')||'light');renderStats();renderBots();
</script>
</body></html>"""


def market_dashboard_page() -> str:
    return """<!doctype html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>داشبورد زنده شاخص‌های افرا کالا</title>
  <style>""" + base_css() + """
    .meta-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px;position:relative;z-index:1}.meta{background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.20);border-radius:16px;padding:10px 12px;min-width:150px}.meta small{display:block;color:#bfdbfe}.meta b{font-size:16px}.toolbar{display:grid;grid-template-columns:1.5fr .8fr .8fr auto;gap:10px;margin:18px 0}.kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-bottom:16px}.kpi{padding:18px}.kpi .label{font-size:13px;color:var(--muted)}.kpi .value{font-size:30px;font-weight:900;margin:6px 0}.kpi .hint{font-size:12px;color:var(--muted)}.green{color:var(--accent)}.red{color:var(--danger)}.orange{color:var(--warn)}.blue{color:var(--brand2)}.section{padding:18px;margin-bottom:16px}.section-head{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:12px}.section h3{margin:0;font-size:18px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}.rate-card{padding:16px;border-radius:20px;background:linear-gradient(180deg,var(--surface),var(--surface2));border:1px solid var(--line);position:relative;overflow:hidden}.rate-card:before{content:"";position:absolute;inset:0 0 auto 0;height:4px;background:linear-gradient(90deg,var(--brand2),#22c55e)}.rate-title{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}.price{font-size:28px;font-weight:950;direction:ltr;text-align:left;margin:10px 0 2px;font-family:var(--mono)}.source-row{display:flex;justify-content:space-between;gap:8px;border-top:1px dashed var(--line);padding-top:10px;margin-top:10px;font-size:12px;color:var(--muted)}.table-wrap{max-height:520px;overflow:auto;border-radius:18px;border:1px solid var(--line)}table{width:100%;border-collapse:separate;border-spacing:0;background:var(--surface);font-size:13px}th,td{padding:11px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}th{position:sticky;top:0;background:var(--surface2);z-index:2;color:var(--muted);font-weight:800}tr:hover td{background:rgba(37,99,235,.04)}.error{max-width:360px;white-space:normal;color:var(--danger)}.empty{padding:24px;text-align:center;color:var(--muted)}.statusbar{position:fixed;left:18px;bottom:18px;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:10px 12px;box-shadow:var(--shadow);font-size:12px;color:var(--muted);z-index:20}.toast{position:fixed;right:18px;bottom:18px;background:#0f172a;color:white;padding:12px 14px;border-radius:16px;box-shadow:var(--shadow);display:none;z-index:30}.toast.show{display:block}@media(max-width:1000px){.toolbar{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.kpis{grid-template-columns:1fr}.price{font-size:23px}}
  </style>
</head><body><div class="wrap"><header class="hero"><div class="hero-top"><div><div class="badge"><span class="dot"></span><span>Live Market Intelligence</span></div><h1 class="title">داشبورد زنده شاخص‌های بازار افرا کالا</h1><p class="subtitle">نمایش زنده نرخ‌ها، سلامت منابع، خطاها و خروجی آماده برای API دستیار هوشمند افرا کالا</p></div><div class="hero-actions"><a class="btn btn-ghost" href="/">بازگشت به صفحه ربات‌ها</a><button class="btn btn-primary" onclick="runNow()">اجرای فوری ربات</button><button class="btn btn-ghost" onclick="loadLive(true)">به‌روزرسانی دستی</button><a class="btn btn-ghost" href="/api/live" target="_blank">JSON زنده</a></div></div><div class="meta-row"><div class="meta"><small>زمان سرور</small><b id="serverTime">—</b></div><div class="meta"><small>وضعیت اتصال</small><b id="streamState">در حال اتصال...</b></div><div class="meta"><small>آخرین عملیات</small><b id="statusText">آماده</b></div></div></header><div class="toolbar"><input id="searchBox" class="control" placeholder="جستجو در شاخص، منبع یا نوع قیمت..." oninput="applyFilters()"><select id="statusFilter" class="control" onchange="applyFilters()"><option value="all">همه وضعیت‌ها</option><option value="ok">فقط سالم</option><option value="bad">فقط خطادار</option></select><select id="kindFilter" class="control" onchange="applyFilters()"><option value="all">همه قیمت‌ها</option><option value="current">current</option><option value="buy">buy</option><option value="sell">sell</option></select><button class="btn theme-btn" onclick="toggleTheme()">تغییر تم</button></div><div class="kpis" id="kpis"></div><section class="card section"><div class="section-head"><div><h3>کارت شاخص‌ها</h3><div class="muted">خلاصه مدیریتی از آخرین snapshot هر شاخص</div></div><span class="pill" id="snapshotCount">—</span></div><div class="grid" id="snapshotCards"></div></section><section class="card section"><div class="section-head"><div><h3>منابع و Observationهای اخیر</h3><div class="muted">برای عیب‌یابی سریع منابع و بررسی سلامت استخراج</div></div><span class="pill" id="observationCount">—</span></div><div class="table-wrap"><table><thead><tr><th>شاخص</th><th>منبع</th><th>نوع</th><th>قیمت</th><th>وضعیت</th><th>تاخیر</th><th>زمان</th><th>خطا</th></tr></thead><tbody id="observations"></tbody></table></div></section></div><div class="statusbar" id="statusbar">در انتظار داده...</div><div class="toast" id="toast"></div><script>
let latestData={snapshots:[],recent_observations:[]};function fmt(n){if(n===null||n===undefined||n==='')return '—';let num=Number(n);return Number.isFinite(num)?num.toLocaleString('en-US'):String(n)}function esc(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}function parsePayload(row){try{return JSON.parse(row.payload_json||'{}')}catch(e){return {}}}function toast(msg){const t=document.getElementById('toast');t.innerText=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3200)}function toggleTheme(){const root=document.documentElement;const next=root.getAttribute('data-theme')==='dark'?'light':'dark';root.setAttribute('data-theme',next);localStorage.setItem('afraTheme',next)}function initTheme(){document.documentElement.setAttribute('data-theme',localStorage.getItem('afraTheme')||'light')}function getFilteredObs(){const q=document.getElementById('searchBox').value.trim().toLowerCase();const st=document.getElementById('statusFilter').value;const kind=document.getElementById('kindFilter').value;return (latestData.recent_observations||[]).filter(r=>{const p=parsePayload(r);const hay=[p.indicator_name,r.indicator_code,p.source_name,r.source_code,r.price_kind,r.error].join(' ').toLowerCase();if(q&&!hay.includes(q))return false;if(st==='ok'&&r.ok!==1)return false;if(st==='bad'&&r.ok===1)return false;if(kind!=='all'&&r.price_kind!==kind)return false;return true})}function healthClass(ok,total){if(!total)return 'bad';const ratio=ok/total;if(ratio>=.75)return 'ok';if(ratio>=.4)return 'warn';return 'bad'}function renderKpis(snaps,obs){const ok=obs.filter(x=>x.ok===1).length;const bad=obs.length-ok;const activeSources=obs.length;const avgLatency=obs.length?Math.round(obs.reduce((a,b)=>a+(b.latency_ms||0),0)/obs.length):0;document.getElementById('kpis').innerHTML=`<div class="card kpi"><div class="label">تعداد شاخص</div><div class="value blue">${snaps.length}</div><div class="hint">snapshotهای زنده</div></div><div class="card kpi"><div class="label">منابع فعال اخیر</div><div class="value">${activeSources}</div><div class="hint">Observationهای ذخیره‌شده</div></div><div class="card kpi"><div class="label">منابع سالم</div><div class="value green">${ok}</div><div class="hint">آخرین وضعیت OK</div></div><div class="card kpi"><div class="label">خطادار</div><div class="value red">${bad}</div><div class="hint">نیازمند بررسی</div></div><div class="card kpi"><div class="label">میانگین تاخیر</div><div class="value orange">${avgLatency}</div><div class="hint">میلی‌ثانیه</div></div>`}function renderSnapshots(snaps){document.getElementById('snapshotCount').innerText=snaps.length+' شاخص';document.getElementById('snapshotCards').innerHTML=snaps.length?snaps.map(s=>{const cls=healthClass(s.ok_count,s.source_count);return `<div class="rate-card"><div class="rate-title"><b>${esc(s.indicator_name)}</b><span class="pill ${cls}">${s.ok_count}/${s.source_count} منبع سالم</span></div><div class="price">${fmt(s.value_toman)}</div><div class="muted">واحد: ${esc(s.unit||'toman')} · روش: ${esc(s.method||'median')}</div><div class="source-row"><span>${esc(s.indicator_code)}</span><span>${esc(s.created_at_jalali)} ${esc(s.created_time_iran)}</span></div></div>`}).join(''):`<div class="empty">هنوز snapshot ثبت نشده است.</div>`}function renderObservations(){const obs=getFilteredObs();document.getElementById('observationCount').innerText=obs.length+' ردیف';document.getElementById('observations').innerHTML=obs.length?obs.map(r=>{const p=parsePayload(r);const ok=r.ok===1;return `<tr><td>${esc(p.indicator_name||r.indicator_code)}</td><td>${esc(p.source_name||r.source_code)}</td><td><span class="pill">${esc(r.price_kind)}</span></td><td class="ltr">${fmt(r.value_toman)}</td><td>${ok?'<span class="pill ok">سالم</span>':'<span class="pill bad">خطا</span>'}</td><td class="ltr">${r.latency_ms||'—'} ms</td><td>${esc(r.observed_at_jalali)} ${esc(r.observed_time_iran)}</td><td class="error">${esc(r.error||'')}</td></tr>`}).join(''):`<tr><td colspan="8" class="empty">موردی با این فیلتر پیدا نشد.</td></tr>`}function render(data){latestData=data||latestData;const time=latestData.server_time||{};document.getElementById('serverTime').innerText=(time.jalali_date_fa||'—')+' '+(time.iran_time_fa||'');const snaps=latestData.snapshots||[];const obs=latestData.recent_observations||[];renderKpis(snaps,obs);renderSnapshots(snaps);renderObservations();document.getElementById('statusbar').innerText='آخرین دریافت: '+(time.iran_time_fa||'—')+' | شاخص‌ها: '+snaps.length+' | observation: '+obs.length}function applyFilters(){renderObservations()}async function loadLive(manual=false){try{const r=await fetch('/api/live');render(await r.json());if(manual)toast('آخرین داده‌ها دریافت شد')}catch(e){document.getElementById('statusText').innerText='خطا در دریافت داده'}}async function runNow(){document.getElementById('statusText').innerText='در حال اجرای فوری...';try{const r=await fetch('/api/run-once',{method:'POST'});const j=await r.json();document.getElementById('statusText').innerText=j.status==='ok'?'اجرای فوری موفق':'خطا در اجرای فوری';toast(j.status==='ok'?'ربات اجرا شد':'خطا: '+(j.error||''));await loadLive()}catch(e){document.getElementById('statusText').innerText='خطا در اجرای فوری'}}function startStream(){const es=new EventSource('/api/stream');es.onopen=()=>{document.getElementById('streamState').innerText='زنده و متصل'};es.onmessage=(ev)=>render(JSON.parse(ev.data));es.onerror=()=>{document.getElementById('streamState').innerText='قطع؛ polling فعال شد';es.close();setInterval(loadLive,5000)}}initTheme();loadLive();startStream();
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return portal_page()


@app.get("/bots/market-data", response_class=HTMLResponse)
def market_data_panel():
    return market_dashboard_page()


@app.get("/dashboard")
def old_dashboard_redirect():
    return RedirectResponse(url="/bots/market-data")


@app.get("/api/bots")
def api_bots():
    return JSONResponse(_load_bots_config())


@app.get("/favicon.ico")
def favicon():
    svg = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='16' fill='#1d4ed8'/><path d='M16 42 28 20l7 13 5-9 8 18z' fill='white'/></svg>"""
    return Response(content=svg, media_type="image/svg+xml")


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
