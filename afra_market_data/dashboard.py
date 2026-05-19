from __future__ import annotations

import html
import json
from collections import Counter, defaultdict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from .core import jalali_stamp, latest_rows, load_config, run_once

app = FastAPI(title="Afra Market Data Dashboard")
CONFIG = "configs/indicators.json"


def fa_digits(value) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def safe(value) -> str:
    return html.escape("" if value is None else str(value))


def load_payload(row: dict) -> dict:
    try:
        return json.loads(row.get("payload") or "{}")
    except Exception:
        return {}


def unit_label(unit: str | None) -> str:
    labels = {"toman": "تومان", "rial": "ریال", "irr": "ریال", "usd": "دلار"}
    return labels.get((unit or "").lower(), unit or "-")


def fmt_value(value) -> str:
    if value is None:
        return "-"
    try:
        v = float(value)
        if v.is_integer():
            return f"{int(v):,}"
        return f"{v:,.4f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def human_error(error: str | None) -> tuple[str, str]:
    if not error:
        return "", ""
    e = str(error)
    low = e.lower()
    if "out of expected range" in low:
        return "عدد استخراج‌شده خارج از بازه معتبر این شاخص است.", e
    if "regex not matched" in low:
        return "الگوی استخراج با محتوای فعلی صفحه هماهنگ نیست.", e
    if "number not found" in low:
        return "عدد قیمت در خروجی منبع پیدا نشد.", e
    if "selector not found" in low or "css selector not found" in low:
        return "مسیر انتخابگر قیمت در صفحه پیدا نشد.", e
    if "timeout" in low:
        return "پاسخ منبع بیش از حد طول کشید.", e
    if "connection" in low or "http" in low:
        return "ارتباط با منبع ناموفق بود.", e
    return "خطای فنی در استخراج منبع رخ داد.", e


def indicator_units(config: dict) -> dict:
    return {i.get("code"): i.get("unit", "unit") for i in config.get("indicators", [])}


def page(rows, config: dict):
    stamp = jalali_stamp()
    latest = rows[:150]
    units = indicator_units(config)

    ok_count = sum(1 for row in latest if row.get("ok"))
    err_count = len(latest) - ok_count
    success_rate = round((ok_count / len(latest)) * 100) if latest else 0

    indicator_codes = set()
    source_codes = set()
    by_indicator = defaultdict(list)

    for row in latest:
        payload = load_payload(row)
        indicator_code = payload.get("indicator_code") or row.get("indicator_code") or "unknown"
        indicator_name = payload.get("indicator_name") or indicator_code
        indicator_codes.add(indicator_code)
        source_codes.add(payload.get("source_code") or row.get("source_code") or "unknown")
        by_indicator[(indicator_code, indicator_name)].append(row)

    summary_cards = []
    for (code, name), group in list(by_indicator.items())[:12]:
        values = [g.get("value_toman") for g in group if g.get("ok") and g.get("value_toman") is not None]
        last_value = fmt_value(values[0]) if values else "-"
        valid = len(values)
        total = len(group)
        health = round(valid / total * 100) if total else 0
        css = "good" if health >= 70 else ("warn" if health >= 40 else "danger")
        summary_cards.append(f"""
          <div class="mini-card {css}">
            <div class="mini-top"><span>{safe(name)}</span><b>{fa_digits(health)}٪</b></div>
            <div class="mini-value">{safe(last_value)} <small>{safe(unit_label(units.get(code)))}</small></div>
            <div class="mini-meta">{fa_digits(valid)} منبع سالم از {fa_digits(total)}</div>
          </div>
        """)

    error_counter = Counter()
    for row in latest:
        if not row.get("ok"):
            readable, _ = human_error(row.get("error"))
            if readable:
                error_counter[readable] += 1
    error_items = "".join(f"<li><span>{safe(k)}</span><b>{fa_digits(v)}</b></li>" for k, v in error_counter.items())
    if not error_items:
        error_items = "<li><span>فعلاً خطای فعالی ثبت نشده است.</span><b>۰</b></li>"

    table_rows = []
    for row in latest:
        payload = load_payload(row)
        ok = bool(row.get("ok"))
        indicator_code = payload.get("indicator_code") or row.get("indicator_code") or ""
        indicator_name = payload.get("indicator_name") or indicator_code
        source_name = payload.get("source_name") or row.get("source_code") or ""
        price_kind = payload.get("price_kind") or row.get("price_kind") or ""
        value = fmt_value(row.get("value_toman"))
        unit = unit_label(units.get(indicator_code) or payload.get("input_unit"))
        time_text = f"{payload.get('collected_time_iran','')}  {payload.get('collected_at_jalali','')}"
        badge = '<span class="badge ok">سالم</span>' if ok else '<span class="badge bad">خطا</span>'
        readable, technical = human_error(row.get("error"))
        error_html = ""
        if readable:
            error_html = f"<div class='err-main'>{safe(readable)}</div><details><summary>جزئیات فنی</summary><code>{safe(technical)}</code></details>"
        table_rows.append(f"""
          <tr class="{'row-ok' if ok else 'row-bad'}">
            <td><strong>{safe(indicator_name)}</strong><small>{safe(indicator_code)}</small></td>
            <td>{safe(source_name)}</td>
            <td><span class="kind">{safe(price_kind)}</span></td>
            <td class="price"><b>{safe(value)}</b><small>{safe(unit)}</small></td>
            <td>{badge}</td>
            <td class="error-cell">{error_html}</td>
            <td class="time-cell">{safe(time_text)}</td>
          </tr>
        """)

    rows_html = "".join(table_rows) or "<tr><td colspan='7'>هنوز داده‌ای ثبت نشده است. دکمه اجرای فوری ربات را بزن.</td></tr>"

    return f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>داشبورد شاخص‌های افرا کالا</title>
<style>
:root{{--bg:#f3f6fb;--card:rgba(255,255,255,.95);--text:#101828;--muted:#667085;--line:#e6edf7;--green:#079455;--red:#d92d20;--amber:#f79009;--blue:#2563eb;--purple:#6941c6}}
*{{box-sizing:border-box}}body{{margin:0;font-family:Tahoma,Arial,sans-serif;color:var(--text);background:radial-gradient(circle at 10% 0%,#dbeafe 0,transparent 28%),radial-gradient(circle at 88% 8%,#ffe4e6 0,transparent 30%),linear-gradient(180deg,#fbfdff 0%,var(--bg) 100%)}}
.wrap{{max-width:1320px;margin:24px auto;padding:0 18px 42px}}
.hero{{background:linear-gradient(135deg,#111827,#1d4ed8 58%,#7c3aed);color:white;border-radius:30px;padding:30px;box-shadow:0 26px 70px rgba(17,24,39,.22);display:grid;grid-template-columns:1.2fr .8fr;gap:20px;align-items:center;overflow:hidden;position:relative}}
.hero:before{{content:"";position:absolute;inset:-80px auto auto -80px;width:260px;height:260px;border-radius:50%;background:rgba(255,255,255,.12)}}.hero h1{{margin:0 0 12px;font-size:31px}}.hero p{{margin:0;color:rgba(255,255,255,.78);line-height:1.9}}
.clock-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:18px;max-width:560px}}.clock-box{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);border-radius:18px;padding:12px}}.clock-box span{{display:block;color:rgba(255,255,255,.68);font-size:12px;margin-bottom:6px}}.clock-box b{{font-size:18px;direction:ltr}}
.actions{{display:flex;gap:10px;flex-wrap:wrap;position:relative;z-index:2}}button,a.btn{{border:0;background:white;color:#111827;padding:12px 16px;border-radius:15px;text-decoration:none;cursor:pointer;font-weight:800;box-shadow:0 12px 28px rgba(0,0,0,.14)}}button.primary{{background:#22c55e;color:white}}#msg{{width:100%;color:rgba(255,255,255,.9);font-weight:800;margin-top:8px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:18px 0}}.stat,.panel,.mini-card{{background:var(--card);border:1px solid rgba(255,255,255,.75);border-radius:24px;box-shadow:0 18px 48px rgba(17,24,39,.08);backdrop-filter:blur(10px)}}.stat{{padding:18px}}.stat .label{{color:var(--muted);font-size:13px}}.stat .num{{font-size:31px;font-weight:950;margin-top:8px;direction:ltr;text-align:right}}.stat.ok .num{{color:var(--green)}}.stat.bad .num{{color:var(--red)}}.stat.blue .num{{color:var(--blue)}}.stat.purple .num{{color:var(--purple)}}
.panel{{padding:18px;margin-top:16px}}.panel-head{{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px}}.panel h2{{margin:0;font-size:20px}}.search{{width:340px;max-width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:15px;outline:none;background:#fff}}
.mini-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.mini-card{{padding:15px;position:relative;overflow:hidden}}.mini-card:before{{content:"";position:absolute;right:0;top:0;width:5px;height:100%;background:var(--blue)}}.mini-card.good:before{{background:var(--green)}}.mini-card.warn:before{{background:var(--amber)}}.mini-card.danger:before{{background:var(--red)}}.mini-top{{display:flex;justify-content:space-between;color:var(--muted);font-size:13px}}.mini-value{{font-size:22px;font-weight:950;margin:10px 0 5px;direction:ltr;text-align:right}}.mini-value small{{font-size:12px;color:var(--muted);font-weight:500;margin-right:4px}}.mini-meta{{font-size:12px;color:var(--muted)}}
.error-list{{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}}.error-list li{{display:flex;justify-content:space-between;gap:12px;background:#fff7ed;border:1px solid #fed7aa;padding:12px 14px;border-radius:16px;color:#9a3412}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:20px;background:white}}table{{width:100%;border-collapse:separate;border-spacing:0}}th{{background:#f8fafc;color:#475467;font-size:13px;text-align:right;padding:14px;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:1}}td{{padding:14px;border-bottom:1px solid var(--line);vertical-align:middle}}tr:hover td{{background:#f9fbff}}td small{{display:block;color:var(--muted);font-size:11px;margin-top:4px}}
.price{{direction:ltr;text-align:right;font-size:16px;white-space:nowrap}}.price b{{font-weight:950}}.price small{{display:inline;color:var(--muted);margin-right:6px}}.kind{{background:#eef4ff;color:#3538cd;border-radius:999px;padding:5px 10px;font-size:12px}}.badge{{display:inline-flex;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:900}}.badge.ok{{background:#ecfdf3;color:var(--green)}}.badge.bad{{background:#fef3f2;color:var(--red)}}.row-bad td{{background:linear-gradient(90deg,rgba(254,243,242,.55),transparent)}}.err-main{{color:var(--red);font-weight:800;margin-bottom:5px}}details summary{{color:var(--muted);cursor:pointer;font-size:12px}}code{{display:block;direction:ltr;text-align:left;white-space:normal;background:#fff1f3;padding:8px;border-radius:10px;margin-top:6px;color:#7a271a}}.time-cell{{color:var(--muted);white-space:nowrap}}.footer-note{{color:var(--muted);font-size:12px;margin-top:12px;line-height:1.8}}
@media(max-width:980px){{.hero,.grid,.mini-grid,.error-list{{grid-template-columns:1fr}}button,a.btn{{width:100%;text-align:center}}}}
</style>
</head>
<body><div class="wrap">
<section class="hero"><div><h1>داشبورد شاخص‌های بازار افرا کالا</h1><p>مرکز کنترل استخراج، کیفیت منابع، داده‌های معتبر، خطاها و خروجی آماده برای API دستیار هوشمند افرا کالا.</p><div class="clock-grid"><div class="clock-box"><span>تاریخ شمسی</span><b>{stamp['jalali_date_fa']}</b></div><div class="clock-box"><span>ساعت ایران</span><b>{stamp['iran_time_fa']}</b></div><div class="clock-box"><span>تاریخ میلادی</span><b id="greg-date">-</b></div><div class="clock-box"><span>ساعت سیستم</span><b id="live-time">-</b></div></div><div id="msg"></div></div><div class="actions"><button class="primary" onclick="runNow()">اجرای فوری ربات</button><a class="btn" href="/api/latest">خروجی JSON</a><a class="btn" href="/">رفرش داشبورد</a></div></section>
<section class="grid"><div class="stat purple"><div class="label">شاخص‌های فعال</div><div class="num">{fa_digits(len(indicator_codes))}</div></div><div class="stat blue"><div class="label">منابع پایش‌شده</div><div class="num">{fa_digits(len(source_codes))}</div></div><div class="stat ok"><div class="label">استخراج سالم</div><div class="num">{fa_digits(ok_count)}</div></div><div class="stat bad"><div class="label">استخراج دارای خطا</div><div class="num">{fa_digits(err_count)}</div></div></section>
<section class="panel"><div class="panel-head"><h2>خلاصه شاخص‌ها</h2><span class="badge ok">نرخ سلامت: {fa_digits(success_rate)}٪</span></div><div class="mini-grid">{''.join(summary_cards) or '<div class="mini-card">هنوز داده‌ای ثبت نشده است.</div>'}</div></section>
<section class="panel"><div class="panel-head"><h2>خطاهای مهم</h2></div><ul class="error-list">{error_items}</ul></section>
<section class="panel"><div class="panel-head"><h2>آخرین استخراج‌ها</h2><input class="search" id="q" placeholder="جستجو در شاخص، منبع، وضعیت یا خطا..." onkeyup="filterRows()"></div><div class="table-wrap"><table id="results"><thead><tr><th>شاخص</th><th>منبع</th><th>نوع قیمت</th><th>مقدار</th><th>وضعیت</th><th>توضیح خطا</th><th>زمان ایران</th></tr></thead><tbody>{rows_html}</tbody></table></div><div class="footer-note">نکته: عددهای خارج از بازه معتبر هر شاخص دیگر سالم حساب نمی‌شوند و وارد میانگین تصمیم‌گیری نمی‌شوند.</div></section>
</div><script>
function pad(n){{return String(n).padStart(2,'0')}}function toFa(s){{return String(s).replace(/[0-9]/g,d=>'۰۱۲۳۴۵۶۷۸۹'[d])}}function updateClock(){{const now=new Date();document.getElementById('greg-date').innerText=toFa(now.getFullYear()+'-'+pad(now.getMonth()+1)+'-'+pad(now.getDate()));document.getElementById('live-time').innerText=toFa(pad(now.getHours())+':'+pad(now.getMinutes())+':'+pad(now.getSeconds()))}}setInterval(updateClock,1000);updateClock();
async function runNow(){{const msg=document.getElementById('msg');msg.innerText='در حال اجرای ربات و دریافت آخرین داده‌ها...';try{{const r=await fetch('/api/run-once',{{method:'POST'}});const j=await r.json();msg.innerText='اجرا کامل شد. تعداد snapshot: '+toFa(j.snapshots||0);setTimeout(()=>location.reload(),900)}}catch(e){{msg.innerText='خطا در اجرای ربات: '+e}}}}
function filterRows(){{const q=document.getElementById('q').value.toLowerCase();document.querySelectorAll('#results tbody tr').forEach(tr=>{{tr.style.display=tr.innerText.toLowerCase().includes(q)?'':'none'}})}}
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    cfg = load_config(CONFIG)
    return page(latest_rows(cfg.get("app", {}).get("sqlite_path", "data/market_data.db")), cfg)


@app.post("/api/run-once")
def api_run_once():
    payload = run_once(CONFIG)
    return {"status": "ok", "snapshots": len(payload["snapshots"])}


@app.get("/api/latest")
def api_latest():
    cfg = load_config(CONFIG)
    return JSONResponse(latest_rows(cfg.get("app", {}).get("sqlite_path", "data/market_data.db")))
