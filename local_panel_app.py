from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'configs' / 'bots.json'
GOOGLE_MAPS_RUNNER = BASE_DIR / 'google-maps-bot' / 'run.py'
GOOGLE_MAPS_OUTPUT_DIR = BASE_DIR / 'google-maps-bot' / 'output'
GOOGLE_MAPS_LOG_DIR = BASE_DIR / 'google-maps-bot' / 'logs'
JOB_QUEUE_PATH = BASE_DIR / 'data' / 'panel_job_requests.jsonl'
INPUT_SETTINGS_PATH = BASE_DIR / 'data' / 'panel_google_maps_inputs.json'
MANAGE_SETTINGS_PATH = BASE_DIR / 'data' / 'panel_google_maps_manage.json'
OUTPUTS_PATH = BASE_DIR / 'data' / 'panel_outputs_registry.json'
LOGS_PATH = BASE_DIR / 'data' / 'panel_logs_registry.json'
WORKER_STATE_PATH = BASE_DIR / 'data' / 'panel_worker_state.json'
UI_PATH = BASE_DIR / 'panel_ui.html'
ADMIN_PASSWORD = os.getenv('AFRA_PANEL_ADMIN_PASSWORD', '')

app = FastAPI(title='Afra Local Panel')


def auth_enabled() -> bool:
    return bool(ADMIN_PASSWORD)


def require_admin(x_panel_password: str | None = Header(default=None)) -> None:
    if ADMIN_PASSWORD and x_panel_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail='unauthorized')


def load_portal_config() -> dict:
    if not CONFIG_PATH.exists():
        return {'portal': {'title': 'Afra Local Panel'}, 'bots': []}
    with CONFIG_PATH.open('r', encoding='utf-8') as file:
        return json.load(file)


def read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open('r', encoding='utf-8') as file:
        return json.load(file)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def list_files(folder: Path) -> list[dict]:
    if not folder.exists():
        return []
    items = []
    for path in sorted(folder.glob('*'), key=lambda p: p.stat().st_mtime, reverse=True):
        if path.is_file():
            items.append({'name': path.name, 'path': str(path), 'size': path.stat().st_size})
    return items


def safe_output_file(file_name: str) -> Path:
    path = (GOOGLE_MAPS_OUTPUT_DIR / file_name).resolve()
    if GOOGLE_MAPS_OUTPUT_DIR.resolve() not in path.parents or not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail='file not found')
    return path


def path_status(path: Path) -> dict:
    return {'path': str(path), 'exists': path.exists()}


@app.get('/', response_class=HTMLResponse)
def home():
    if UI_PATH.exists():
        return UI_PATH.read_text(encoding='utf-8')
    return '<h1>Afra Local Panel</h1><p>Use /docs for API testing.</p>'


@app.get('/api/health')
def health():
    return {'status': 'ok', 'paths': {'runner': path_status(GOOGLE_MAPS_RUNNER), 'output_dir': path_status(GOOGLE_MAPS_OUTPUT_DIR), 'log_dir': path_status(GOOGLE_MAPS_LOG_DIR), 'ui': path_status(UI_PATH)}}


@app.get('/api/auth-mode')
def panel_auth_mode():
    return {'auth_enabled': auth_enabled()}


@app.get('/api/bots')
def bots():
    config = load_portal_config()
    return {'bots': config.get('bots', [])}


@app.get('/api/google-maps/worker-state')
def google_maps_worker_state():
    return read_json(WORKER_STATE_PATH, {'status': 'unknown'})


@app.get('/api/google-maps/runner-exists')
def google_maps_runner_exists():
    return {'exists': GOOGLE_MAPS_RUNNER.exists()}


@app.post('/api/google-maps/request-run')
def request_google_maps_run(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    JOB_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    item = {'bot_id': 'google_maps_leads', 'status': 'requested'}
    with JOB_QUEUE_PATH.open('a', encoding='utf-8') as file:
        file.write(json.dumps(item, ensure_ascii=False) + '\n')
    return {'accepted': True, 'queue': str(JOB_QUEUE_PATH)}


@app.get('/api/google-maps/queue')
def google_maps_queue():
    if not JOB_QUEUE_PATH.exists():
        return {'jobs': [], 'total': 0}
    jobs = []
    with JOB_QUEUE_PATH.open('r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:
                jobs.append(json.loads(line))
    return {'jobs': jobs, 'total': len(jobs)}


@app.get('/api/google-maps/inputs')
def get_google_maps_inputs():
    return read_json(INPUT_SETTINGS_PATH, {'items': []})


@app.post('/api/google-maps/inputs/save')
def save_google_maps_inputs(data: dict, x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    items = data.get('items')
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail='items must be a list')
    write_json(INPUT_SETTINGS_PATH, {'items': items})
    return {'saved': True, 'total': len(items), 'data': {'items': items}}


@app.get('/api/google-maps/manage')
def get_google_maps_manage():
    return read_json(MANAGE_SETTINGS_PATH, {'execution_window': {'start': '00:00', 'end': '23:59'}, 'limits': {'max_queries': 10, 'max_businesses_per_query': 50}, 'delays': {'between_queries': '20-60', 'between_clicks': '5-15'}, 'status': 'pause'})


@app.get('/api/google-maps/outputs')
def get_google_maps_outputs():
    registry = read_json(OUTPUTS_PATH, {'items': []})
    return {'items': registry.get('items', []), 'files': list_files(GOOGLE_MAPS_OUTPUT_DIR)}


@app.get('/api/google-maps/logs')
def get_google_maps_logs():
    registry = read_json(LOGS_PATH, {'items': []})
    return {'items': registry.get('items', []), 'files': list_files(GOOGLE_MAPS_LOG_DIR)}


@app.get('/api/google-maps/downloads')
def get_google_maps_downloads():
    return {'items': list_files(GOOGLE_MAPS_OUTPUT_DIR)}


@app.get('/api/google-maps/download/{file_name}')
def download_google_maps_output(file_name: str):
    path = safe_output_file(file_name)
    return FileResponse(str(path), filename=path.name)


@app.post('/api/google-maps/inputs/sample')
def create_sample_google_maps_input(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'items': [{'province': 'تهران', 'city': 'تهران', 'keyword': 'فروشگاه لوازم خانگی', 'brand': '', 'related_keywords': '', 'category': 'لوازم خانگی', 'active': True}]}
    write_json(INPUT_SETTINGS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/manage/sample')
def create_sample_google_maps_manage(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'execution_window': {'start': '00:00', 'end': '23:59'}, 'limits': {'max_queries': 10, 'max_businesses_per_query': 50}, 'delays': {'between_queries': '20-60', 'between_clicks': '5-15'}, 'status': 'resume'}
    write_json(MANAGE_SETTINGS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/outputs/sample')
def create_sample_output_registry(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'items': [{'file_name': 'google_maps_results.xlsx', 'records': 120, 'status': 'ready'}]}
    write_json(OUTPUTS_PATH, data)
    return {'saved': True, 'data': data}


@app.post('/api/google-maps/logs/sample')
def create_sample_logs_registry(x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    data = {'items': [{'level': 'INFO', 'message': 'Google Maps panel log registry initialized'}]}
    write_json(LOGS_PATH, data)
    return {'saved': True, 'data': data}

# ─── Divar API ───────────────────────────────────────────────
import sqlite3, subprocess, sys
from pathlib import Path

DIVAR_DB_PATH = BASE_DIR / 'data' / 'divar_leads.db'
DIVAR_LOG_PATH = BASE_DIR / 'logs' / 'divar_bot.log'
DIVAR_RUN_PY   = BASE_DIR / 'divar-bot' / 'run.py'

def divar_db():
    return sqlite3.connect(str(DIVAR_DB_PATH))

@app.get('/api/divar/stats')
def divar_stats():
    if not DIVAR_DB_PATH.exists():
        return {"total_leads": 0, "synced": 0, "messages_sent": 0, "pending": 0, "failed": 0}
    conn = divar_db()
    total    = conn.execute("SELECT COUNT(*) FROM divar_leads").fetchone()[0]
    synced   = conn.execute("SELECT COUNT(*) FROM divar_leads WHERE sync_status='synced'").fetchone()[0]
    messages = conn.execute("SELECT COUNT(*) FROM divar_leads WHERE message_sent=1").fetchone()[0]
    pending  = conn.execute("SELECT COUNT(*) FROM divar_leads WHERE extraction_status='pending'").fetchone()[0]
    failed   = conn.execute("SELECT COUNT(*) FROM divar_leads WHERE extraction_status='failed'").fetchone()[0]
    conn.close()
    return {"total_leads": total, "synced": synced, "messages_sent": messages, "pending": pending, "failed": failed}

@app.get('/api/divar/leads')
def divar_leads(limit: int = 50, offset: int = 0, status: str | None = None):
    if not DIVAR_DB_PATH.exists():
        return {"items": [], "total": 0}
    conn = divar_db()
    where = f"WHERE extraction_status='{status}'" if status else ""
    total = conn.execute(f"SELECT COUNT(*) FROM divar_leads {where}").fetchone()[0]
    rows  = conn.execute(f"""
        SELECT id, title, seller_name, phone, city, district,
               price_text, extraction_status, message_sent,
               message_status, sync_status, source_url, created_at
        FROM divar_leads {where}
        ORDER BY id DESC LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()
    conn.close()
    keys = ["id","title","seller_name","phone","city","district",
            "price_text","extraction_status","message_sent",
            "message_status","sync_status","source_url","created_at"]
    return {"items": [dict(zip(keys, r)) for r in rows], "total": total}

@app.get('/api/divar/logs')
def divar_logs(lines: int = 100):
    if not DIVAR_LOG_PATH.exists():
        return {"lines": []}
    all_lines = DIVAR_LOG_PATH.read_text(encoding='utf-8', errors='replace').splitlines()
    return {"lines": all_lines[-lines:]}

@app.post('/api/divar/run')
def divar_run(body: dict, x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    url = body.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="url الزامی است")
    send  = body.get("send_messages", False)
    no_ai = body.get("no_ai", False)
    cmd   = [sys.executable, str(DIVAR_RUN_PY), "--url", url]
    if send:  cmd.append("--send-messages")
    if no_ai: cmd.append("--no-ai")
    try:
        proc = subprocess.Popen(cmd, cwd=str(DIVAR_RUN_PY.parent),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return {"started": True, "pid": proc.pid, "cmd": " ".join(cmd)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/divar/send-log')
def divar_send_log(limit: int = 50):
    if not DIVAR_DB_PATH.exists():
        return {"items": []}
    conn = divar_db()
    rows = conn.execute("""
        SELECT id, lead_id, phone, message_text, status, error_msg, sent_at
        FROM divar_send_log ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    keys = ["id","lead_id","phone","message_text","status","error_msg","sent_at"]
    return {"items": [dict(zip(keys, r)) for r in rows]}


DIVAR_PROFILE_DIR = BASE_DIR / 'runtime' / 'profiles' / 'divar' / 'default'


@app.get('/api/divar/session-status')
def divar_session_status():
    profile_dir = DIVAR_PROFILE_DIR
    exists = profile_dir.exists() and profile_dir.is_dir()

    session_files = []
    if exists:
        session_files = list(profile_dir.glob('**/*.sqlite')) + \
            list(profile_dir.glob('**/Cookies')) + \
            list(profile_dir.glob('**/Local State')) + \
            list(profile_dir.glob('**/Default/Cookies'))

    has_session = len(session_files) > 0

    profiles_dir = BASE_DIR / 'runtime' / 'profiles' / 'divar'
    numbered_profiles = []
    for index in range(1, 6):
        profile_path = profiles_dir / f'divar-profile-{index}'
        metadata_path = profile_path / 'metadata.json'
        if metadata_path.exists():
            try:
                data = json.loads(metadata_path.read_text(encoding='utf-8'))
                numbered_profiles.append({
                    'profile_id': f'divar-profile-{index}',
                    'reputation_score': float(data.get('reputation_score', 1.0)),
                    'success_count': int(data.get('success_count', 0)),
                    'failure_count': int(data.get('failure_count', 0)),
                    'available': True,
                })
            except Exception:
                continue

    return {
        'logged_in': has_session,
        'profile_path': str(profile_dir),
        'session_files_found': len(session_files),
        'numbered_profiles': numbered_profiles,
        'login_instructions': [
            'باز کردن ترمینال در Codespace',
            'اجرای دستور: cd /workspaces/old-dollar-tehran-bot && python3 divar-bot/run.py --login --phone 09XXXXXXXXX',
            'وارد کردن کد OTP که از دیوار دریافت کردید',
            'کلیک روی بررسی مجدد وضعیت در پنل'
        ]
    }


@app.post('/api/divar/login')
def divar_login(body: dict):
    phone = str(body.get('phone', '')).strip()
    if not phone:
        raise HTTPException(status_code=400, detail='phone الزامی است')

    env = os.environ.copy()
    env['DIVAR_HEADLESS'] = '1'
    cmd = [sys.executable, str(DIVAR_RUN_PY), '--login', '--phone', phone]
    try:
        subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    message = (
        'ورود به دیوار در حالت غیرهمزمان شروع شد. در Codespace، ورود باید دستی انجام شود.\n'
        f'در ترمینال زیر را اجرا کنید:\ncd {BASE_DIR} && python3 divar-bot/run.py --login --phone {phone}\n'
        'پس از دریافت کد OTP، آن را در ترمینال وارد کنید و سپس دکمه بررسی مجدد وضعیت را بزنید.'
    )
    return {"started": True, "message": message}


@app.post('/api/divar/session-import')
def divar_session_import(body: dict | None = None):
    profile_dir = DIVAR_PROFILE_DIR
    exists = profile_dir.exists() and profile_dir.is_dir()
    has_files = bool(list(profile_dir.iterdir())) if exists else False
    note = str((body or {}).get('note', '')) if body else ''
    return {"logged_in": exists and has_files, "profile_path": str(profile_dir), "note": note}

# ─── Torob API ───────────────────────────────────────────────
TOROB_DB_PATH  = BASE_DIR / 'data' / 'torob.db'
TOROB_LOG_PATH = BASE_DIR / 'logs' / 'torob_bot.log'
TOROB_RUN_PY   = BASE_DIR / 'torob-bot' / 'run.py'

def torob_db():
    return sqlite3.connect(str(TOROB_DB_PATH))

@app.get('/api/torob/stats')
def torob_stats():
    if not TOROB_DB_PATH.exists():
        return {"total_sellers": 0, "synced": 0, "total_reports": 0, "total_history": 0}
    conn = torob_db()
    sellers  = conn.execute("SELECT COUNT(*) FROM seller_leads").fetchone()[0]
    synced   = conn.execute("SELECT COUNT(*) FROM seller_leads WHERE sync_status='synced'").fetchone()[0]
    reports  = conn.execute("SELECT COUNT(*) FROM price_reports").fetchone()[0]
    history  = conn.execute("SELECT COUNT(*) FROM torob_price_history").fetchone()[0]
    conn.close()
    return {"total_sellers": sellers, "synced": synced, "total_reports": reports, "total_history": history}

@app.get('/api/torob/sellers')
def torob_sellers(limit: int = 50, offset: int = 0, crawl_status: str | None = None):
    if not TOROB_DB_PATH.exists():
        return {"items": [], "total": 0}
    conn = torob_db()
    where = f"WHERE crawl_status='{crawl_status}'" if crawl_status else ""
    total = conn.execute(f"SELECT COUNT(*) FROM seller_leads {where}").fetchone()[0]
    rows  = conn.execute(f"""
        SELECT id, store_name, phone, email, store_url, torob_url,
               price_on_torob, instagram, telegram, whatsapp,
               crawl_status, sync_status, created_at
        FROM seller_leads {where}
        ORDER BY id DESC LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()
    conn.close()
    keys = ["id","store_name","phone","email","store_url","torob_url",
            "price_on_torob","instagram","telegram","whatsapp",
            "crawl_status","sync_status","created_at"]
    return {"items": [dict(zip(keys, r)) for r in rows], "total": total}

@app.get('/api/torob/reports')
def torob_reports(limit: int = 50, offset: int = 0):
    if not TOROB_DB_PATH.exists():
        return {"items": [], "total": 0}
    conn = torob_db()
    total = conn.execute("SELECT COUNT(*) FROM price_reports").fetchone()[0]
    rows  = conn.execute("""
        SELECT id, product_code, product_name, afrakala_price, lowest_rival,
               avg_rival, afrakala_rank, rival_count, diff_percent, sync_status, created_at
        FROM price_reports ORDER BY id DESC LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()
    conn.close()
    keys = ["id","product_code","product_name","afrakala_price","lowest_rival",
            "avg_rival","afrakala_rank","rival_count","diff_percent","sync_status","created_at"]
    return {"items": [dict(zip(keys, r)) for r in rows], "total": total}

@app.get('/api/torob/logs')
def torob_logs(lines: int = 100):
    if not TOROB_LOG_PATH.exists():
        return {"lines": []}
    all_lines = TOROB_LOG_PATH.read_text(encoding='utf-8', errors='replace').splitlines()
    return {"lines": all_lines[-lines:]}

@app.post('/api/torob/run')
def torob_run(body: dict, x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    query = body.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="query الزامی است")
    cmd = [sys.executable, str(TOROB_RUN_PY), query]
    try:
        proc = subprocess.Popen(cmd, cwd=str(TOROB_RUN_PY.parent),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return {"started": True, "pid": proc.pid, "cmd": " ".join(cmd)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
