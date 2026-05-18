from __future__ import annotations

import json, os, re, sqlite3, statistics, time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

FA_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
TEHRAN = timezone(timedelta(hours=3, minutes=30))


def now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def gregorian_to_jalali(gy:int, gm:int, gd:int):
    g_d_m=[0,31,59,90,120,151,181,212,243,273,304,334]
    if gy>1600:
        jy=979; gy-=1600
    else:
        jy=0; gy-=621
    gy2=gy+1 if gm>2 else gy
    days=365*gy+(gy2+3)//4-(gy2+99)//100+(gy2+399)//400-80+gd+g_d_m[gm-1]
    jy+=33*(days//12053); days%=12053
    jy+=4*(days//1461); days%=1461
    if days>365:
        jy+=(days-1)//365; days=(days-1)%365
    jm=1+days//31 if days<186 else 7+(days-186)//30
    jd=1+(days%31 if days<186 else (days-186)%30)
    return jy,jm,jd


def fa_num(v: Any) -> str:
    return str(v).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))


def jalali_stamp(dt: datetime | None = None) -> dict[str,str]:
    dt = dt or now_tehran()
    jy,jm,jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    return {
        'gregorian': dt.isoformat(),
        'jalali_date': f'{jy:04d}/{jm:02d}/{jd:02d}',
        'jalali_date_fa': f'{fa_num(jy)}/{fa_num(jm).zfill(2)}/{fa_num(jd).zfill(2)}',
        'iran_time': dt.strftime('%H:%M:%S'),
        'iran_time_fa': fa_num(dt.strftime('%H:%M:%S')),
    }


def clean_number(text: str) -> int:
    if text is None:
        raise ValueError('empty number')
    s = str(text).translate(FA_DIGITS).replace(',', '').replace('،','').replace(' ', '')
    m = re.search(r'-?\d+', s)
    if not m:
        raise ValueError(f'number not found in {text!r}')
    return int(m.group(0))


def normalize(value: int, unit: str) -> int:
    unit = (unit or 'toman').lower()
    return round(value / 10) if unit in ('rial','irr','ریال') else int(value)

@dataclass
class SourceResult:
    indicator_code: str
    indicator_name: str
    source_code: str
    source_name: str
    price_kind: str
    url: str
    ok: bool
    value_toman: int | None
    raw_value: str | None
    input_unit: str
    error: str | None
    collected_at: str
    collected_at_jalali: str
    collected_time_iran: str


def load_config(path='configs/indicators.json') -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def fetch_html(url: str, timeout: int, user_agent: str) -> str:
    r = requests.get(url, timeout=timeout, headers={'User-Agent': user_agent, 'Accept-Language':'fa,en;q=0.8'})
    r.raise_for_status()
    return r.text


def extract_by_step(html: str, step: dict) -> str:
    kind = step.get('kind')
    soup = BeautifulSoup(html, 'html.parser')
    if kind == 'css':
        el = soup.select_one(step['selector'])
        if not el:
            raise ValueError('css selector not found')
        return el.get_text(' ', strip=True)
    if kind == 'regex':
        m = re.search(step['pattern'], html, re.S)
        if not m:
            raise ValueError('regex not matched')
        return m.group(1) if m.groups() else m.group(0)
    if kind == 'row_contains':
        words = step.get('contains', [])
        for row in soup.find_all(['tr','div','article']):
            txt = row.get_text(' ', strip=True)
            if all(w in txt for w in words):
                pat = step.get('number_pattern', r'([0-9۰-۹٠-٩]{1,3}(?:[,،][0-9۰-۹٠-٩]{3})+)')
                nums = re.findall(pat, txt)
                if nums:
                    return nums[int(step.get('index', 0))]
        raise ValueError('row with requested words not found')
    raise ValueError(f'unknown extractor kind: {kind}')


def extract_source(indicator: dict, source: dict, app: dict) -> SourceResult:
    stamp = jalali_stamp()
    base = dict(
        indicator_code=indicator['code'], indicator_name=indicator['name'],
        source_code=source['code'], source_name=source['name'], price_kind=source.get('price_kind','current'),
        url=source['url'], input_unit=source.get('unit','toman'), collected_at=stamp['gregorian'],
        collected_at_jalali=stamp['jalali_date'], collected_time_iran=stamp['iran_time']
    )
    try:
        if source['url'].startswith('manual://'):
            raw = str(source['manual_value'])
        else:
            page = fetch_html(source['url'], app.get('timeout_seconds',20), app.get('user_agent','Mozilla/5.0'))
            raw = None; last_error = None
            for step in source.get('extractors', []):
                try:
                    raw = extract_by_step(page, step); break
                except Exception as e:
                    last_error = str(e)
            if raw is None:
                raise ValueError(last_error or 'no extractor matched')
        value = normalize(clean_number(raw), source.get('unit','toman'))
        return SourceResult(**base, ok=True, value_toman=value, raw_value=raw, error=None)
    except Exception as e:
        return SourceResult(**base, ok=False, value_toman=None, raw_value=None, error=f'{type(e).__name__}: {e}')


def ensure_db(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute('''create table if not exists results(
        id integer primary key autoincrement, indicator_code text, source_code text, price_kind text,
        ok integer, value_toman integer, raw_value text, error text, payload text, collected_at text
    )''')
    con.execute('''create table if not exists snapshots(
        id integer primary key autoincrement, indicator_code text, indicator_name text,
        value_toman integer, source_count integer, ok_count integer, payload text, created_at text
    )''')
    con.commit(); return con


def save_results(db_path: str, results: list[SourceResult], snapshots: list[dict]):
    con = ensure_db(db_path)
    for r in results:
        con.execute('insert into results(indicator_code,source_code,price_kind,ok,value_toman,raw_value,error,payload,collected_at) values(?,?,?,?,?,?,?,?,?)',
                    (r.indicator_code,r.source_code,r.price_kind,1 if r.ok else 0,r.value_toman,r.raw_value,r.error,json.dumps(asdict(r),ensure_ascii=False),r.collected_at))
    for s in snapshots:
        con.execute('insert into snapshots(indicator_code,indicator_name,value_toman,source_count,ok_count,payload,created_at) values(?,?,?,?,?,?,?)',
                    (s['indicator_code'],s['indicator_name'],s.get('value_toman'),s['source_count'],s['ok_count'],json.dumps(s,ensure_ascii=False),s['created_at']))
    con.commit(); con.close()


def build_snapshots(config: dict, results: list[SourceResult]) -> list[dict]:
    out=[]
    for ind in config['indicators']:
        group=[r for r in results if r.indicator_code==ind['code']]
        good=[r.value_toman for r in group if r.ok and r.value_toman is not None]
        stamp=jalali_stamp()
        out.append({
            'indicator_code': ind['code'], 'indicator_name': ind['name'], 'unit':'toman',
            'value_toman': round(statistics.median(good)) if good else None,
            'source_count': len(group), 'ok_count': len(good),
            'created_at': stamp['gregorian'], 'created_at_jalali': stamp['jalali_date'], 'created_time_iran': stamp['iran_time'],
            'sources': [asdict(r) for r in group]
        })
    return out


def run_once(config_path='configs/indicators.json') -> dict:
    cfg=load_config(config_path); app=cfg.get('app',{})
    results=[]
    for ind in cfg.get('indicators',[]):
        for src in ind.get('sources',[]):
            if src.get('enabled', True):
                results.append(extract_source(ind, src, app))
                time.sleep(app.get('sleep_between_sources_seconds', 0))
    snapshots=build_snapshots(cfg, results)
    save_results(app.get('sqlite_path','data/market_data.db'), results, snapshots)
    payload={'meta': {'project':'afra_market_data','generated_at': jalali_stamp()}, 'snapshots': snapshots}
    Path(app.get('output_dir','output')).mkdir(parents=True, exist_ok=True)
    Path(app.get('output_dir','output'), 'latest_payload.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2), encoding='utf-8')
    return payload


def post_to_afra(payload: dict, config: dict) -> tuple[bool,str]:
    sync=config.get('sync',{})
    if not sync.get('enabled'):
        return False, 'sync disabled'
    url=os.getenv('AFRA_API_URL') or sync.get('api_url')
    token=os.getenv('AFRA_API_TOKEN') or sync.get('api_token')
    if not url:
        return False, 'AFRA_API_URL is empty'
    headers={'Content-Type':'application/json'}
    if token:
        headers['Authorization']=f'Bearer {token}'
    r=requests.post(url, json=payload, headers=headers, timeout=sync.get('timeout_seconds',30))
    return r.ok, f'{r.status_code} {r.text[:300]}'


def latest_rows(db_path='data/market_data.db', limit=100):
    if not Path(db_path).exists():
        return []
    con=sqlite3.connect(db_path); con.row_factory=sqlite3.Row
    rows=con.execute('select * from results order by id desc limit ?', (limit,)).fetchall()
    con.close(); return [dict(x) for x in rows]
