from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import selectors
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

sys.path.insert(0, str(BASE_DIR / 'divar-bot'))
sys.path.insert(0, str(BASE_DIR / 'torob-bot'))

import sys as _sys
_sys.path.insert(0, str(BASE_DIR / 'divar-bot'))
from app.personalizer import load_template, save_template
_sys.path.pop(0)
from app.session_persistence import DivarSessionPersistenceManager
from app.deepseek_analyzer import DeepSeekAnalyzer
from app.excel_exporter import export_to_excel

DIVAR_DB_PATH = BASE_DIR / 'data' / 'divar_leads.db'
DIVAR_LOG_PATH = BASE_DIR / 'logs' / 'divar_bot.log'
DIVAR_RUN_PY   = BASE_DIR / 'divar-bot' / 'run.py'
DIVAR_ENV_PATH = BASE_DIR / 'divar-bot' / '.env'
DIVAR_PROFILE_BASE_DIR = BASE_DIR / 'runtime' / 'profiles' / 'divar'
DIVAR_PROFILE_DIR = DIVAR_PROFILE_BASE_DIR / 'default'
DIVAR_RUN_PROCESS: subprocess.Popen | None = None
DIVAR_LOGIN_PROCESSES: dict[str, subprocess.Popen] = {}
DIVAR_LOGIN_OUTPUTS: dict[str, list[str]] = {}


def divar_db():
    return sqlite3.connect(str(DIVAR_DB_PATH))


def _drain_process_output(proc: subprocess.Popen, buffer: list[str]) -> list[str]:
    if not proc or proc.stdout is None:
        return buffer
    try:
        fd = proc.stdout.fileno()
        os.set_blocking(fd, False)
        try:
            chunk = os.read(fd, 4096)
        except BlockingIOError:
            chunk = b''
        except OSError:
            chunk = b''
        if chunk:
            text = chunk.decode('utf-8', errors='replace')
            for line in text.splitlines():
                if line.strip():
                    buffer.append(line)
            if len(buffer) > 200:
                buffer[:] = buffer[-200:]
    except Exception:
        pass
    return buffer


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _write_env_file(path: Path, updates: dict[str, str]) -> None:
    values = _read_env_file(path)
    values.update({k: str(v) for k, v in updates.items()})
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key in sorted(values):
        lines.append(f"{key}={values[key]}")
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def _mask_secret(value: str | None) -> str:
    if not value:
        return ''
    return value[:2] + '••••' + value[-2:] if len(value) > 4 else '••••'


def _divar_profile_dir(profile_id: str | None = None) -> Path:
    if not profile_id:
        return DIVAR_PROFILE_DIR
    profile_path = DIVAR_PROFILE_BASE_DIR / profile_id
    profile_path.mkdir(parents=True, exist_ok=True)
    return profile_path


def _divar_profile_snapshot() -> list[dict]:
    manager = DivarSessionPersistenceManager(base_dir=DIVAR_PROFILE_BASE_DIR, profile_count=int(os.getenv('DIVAR_PROFILE_COUNT', '5')))
    profiles = manager.snapshot()
    result = []
    for profile in profiles:
        profile_path = Path(profile.get('profile_path', ''))
        session_files = []
        if profile_path.exists():
            session_files = list(profile_path.glob('**/*.sqlite')) + list(profile_path.glob('**/Cookies')) + list(profile_path.glob('**/Local State')) + list(profile_path.glob('**/Default/Cookies'))
        result.append({
            'profile_id': profile.get('profile_id'),
            'reputation_score': float(profile.get('reputation_score', 1.0)),
            'success_count': int(profile.get('success_count', 0)),
            'failure_count': int(profile.get('failure_count', 0)),
            'available': bool(profile.get('available', True)),
            'cooldown_until': float(profile.get('cooldown_until', 0.0)),
            'last_used_at': float(profile.get('last_used_at', 0.0)),
            'has_session_files': bool(session_files),
        })
    return result


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
def divar_leads(limit: int = 50, offset: int = 0, status: str | None = None, city: str | None = None, message_sent: str | None = None):
    if not DIVAR_DB_PATH.exists():
        return {"items": [], "total": 0}
    clauses = []
    params: list[object] = []
    if status:
        clauses.append("extraction_status = ?")
        params.append(status)
    if city:
        clauses.append("city = ?")
        params.append(city)
    if message_sent is not None:
        clauses.append("message_sent = ?")
        params.append(int(message_sent))
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    conn = divar_db()
    total = conn.execute(f"SELECT COUNT(*) FROM divar_leads{where}", params).fetchone()[0]
    rows  = conn.execute(f"""
        SELECT id, title, seller_name, phone, city, district,
               price_text, extraction_status, ai_analysis,
               message_sent, message_status, sync_status, source_url, created_at
        FROM divar_leads{where}
        ORDER BY id DESC LIMIT ? OFFSET ?
    """, [*params, limit, offset]).fetchall()
    conn.close()
    keys = ["id", "title", "seller_name", "phone", "city", "district",
            "price_text", "extraction_status", "ai_analysis",
            "message_sent", "message_status", "sync_status", "source_url", "created_at"]
    return {"items": [dict(zip(keys, r)) for r in rows], "total": total}


@app.get('/api/divar/logs')
def divar_logs(lines: int = 100, level: str | None = None, search: str | None = None):
    if not DIVAR_LOG_PATH.exists():
        return {"lines": []}
    all_lines = DIVAR_LOG_PATH.read_text(encoding='utf-8', errors='replace').splitlines()
    filtered = []
    for line in all_lines[-max(lines, 1):]:
        if level and level.upper() not in line.upper():
            continue
        if search and search.lower() not in line.lower():
            continue
        filtered.append(line)
    return {"lines": filtered[-lines:]}


@app.post('/api/divar/run')
def divar_run(body: dict, x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    url = body.get('url', '')
    if not url:
        raise HTTPException(status_code=400, detail='url الزامی است')
    send = body.get('send_messages', False)
    no_ai = body.get('no_ai', False)
    profile_id = str(body.get('profile_id', '')).strip()
    env = os.environ.copy()
    if profile_id:
        env['DIVAR_PROFILE_DIR'] = str(_divar_profile_dir(profile_id))
    cmd = [sys.executable, str(DIVAR_RUN_PY), '--url', url]
    if send:
        cmd.append('--send-messages')
    if no_ai:
        cmd.append('--no-ai')
    try:
        global DIVAR_RUN_PROCESS
        DIVAR_RUN_PROCESS = subprocess.Popen(cmd, cwd=str(DIVAR_RUN_PY.parent), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        return {'started': True, 'pid': DIVAR_RUN_PROCESS.pid, 'cmd': ' '.join(cmd)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get('/api/divar/run/status')
def divar_run_status():
    global DIVAR_RUN_PROCESS
    if not DIVAR_RUN_PROCESS:
        return {'running': False, 'pid': None, 'output': []}
    output = []
    if DIVAR_RUN_PROCESS.stdout is not None:
        output = _drain_process_output(DIVAR_RUN_PROCESS, output)
    running = DIVAR_RUN_PROCESS.poll() is None
    return {'running': running, 'pid': DIVAR_RUN_PROCESS.pid, 'output': output[-60:]}


@app.post('/api/divar/run/stop')
def divar_run_stop():
    global DIVAR_RUN_PROCESS
    if DIVAR_RUN_PROCESS and DIVAR_RUN_PROCESS.poll() is None:
        DIVAR_RUN_PROCESS.terminate()
        try:
            DIVAR_RUN_PROCESS.wait(timeout=5)
        except Exception:
            DIVAR_RUN_PROCESS.kill()
    DIVAR_RUN_PROCESS = None
    return {'stopped': True}


@app.get('/api/divar/send-log')
def divar_send_log(limit: int = 50):
    if not DIVAR_DB_PATH.exists():
        return {'items': []}
    conn = divar_db()
    rows = conn.execute('''
        SELECT id, lead_id, phone, message_text, status, error_msg, sent_at
        FROM divar_send_log ORDER BY id DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    keys = ['id', 'lead_id', 'phone', 'message_text', 'status', 'error_msg', 'sent_at']
    return {'items': [dict(zip(keys, r)) for r in rows]}


@app.get('/api/divar/accounts')
def divar_accounts():
    items = _divar_profile_snapshot()
    return {'items': items, 'total': len(items)}


@app.post('/api/divar/accounts/{profile_id}/login/start')
def divar_login_start(profile_id: str, body: dict):
    phone = str(body.get('phone', '')).strip()
    if not phone:
        raise HTTPException(status_code=400, detail='phone الزامی است')
    env = os.environ.copy()
    env['DIVAR_HEADLESS'] = '1'
    env['DIVAR_PROFILE_DIR'] = str(_divar_profile_dir(profile_id))
    cmd = ['xvfb-run', '-a', sys.executable, str(DIVAR_RUN_PY), '--login', '--phone', phone]
    proc = subprocess.Popen(cmd, cwd=str(BASE_DIR), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env, start_new_session=True)
    DIVAR_LOGIN_PROCESSES[profile_id] = proc
    DIVAR_LOGIN_OUTPUTS[profile_id] = []
    return {'started': True, 'process_key': profile_id}


@app.post('/api/divar/accounts/{profile_id}/login/otp')
def divar_login_otp(profile_id: str, body: dict):
    otp = str(body.get('otp', '')).strip()
    proc = DIVAR_LOGIN_PROCESSES.get(profile_id)
    if not proc or proc.poll() is not None:
        raise HTTPException(status_code=404, detail='process not found')
    if not otp:
        raise HTTPException(status_code=400, detail='otp الزامی است')
    if proc.stdin is not None:
        proc.stdin.write(otp + '\n')
        proc.stdin.flush()
    return {'sent': True}


@app.get('/api/divar/accounts/{profile_id}/login/status')
def divar_login_status(profile_id: str):
    proc = DIVAR_LOGIN_PROCESSES.get(profile_id)
    buffer = DIVAR_LOGIN_OUTPUTS.get(profile_id, [])
    if proc is not None:
        buffer = _drain_process_output(proc, buffer)
        DIVAR_LOGIN_OUTPUTS[profile_id] = buffer
    running = proc is not None and proc.poll() is None
    output = buffer[-40:]
    success = any('Login موفق' in line for line in output)
    return {'running': running, 'output': output, 'success': success}


@app.delete('/api/divar/accounts/{profile_id}')
def divar_account_delete(profile_id: str):
    profile_path = _divar_profile_dir(profile_id)
    if profile_path.exists():
        shutil.rmtree(profile_path)
    profile_path.mkdir(parents=True, exist_ok=True)
    metadata_path = profile_path / 'metadata.json'
    metadata_path.write_text(json.dumps({'profile_id': profile_id, 'reputation_score': 1.0, 'success_count': 0, 'failure_count': 0, 'cooldown_until': 0.0, 'last_used_at': 0.0}, ensure_ascii=False, indent=2), encoding='utf-8')
    DIVAR_LOGIN_PROCESSES.pop(profile_id, None)
    DIVAR_LOGIN_OUTPUTS.pop(profile_id, None)
    return {'deleted': True, 'profile_id': profile_id}


@app.get('/api/divar/config')
def divar_config():
    return {
        'DIVAR_MAX_ADS_PER_RUN': os.getenv('DIVAR_MAX_ADS_PER_RUN', '200'),
        'DIVAR_DAILY_MESSAGE_LIMIT': os.getenv('DIVAR_DAILY_MESSAGE_LIMIT', '30'),
        'DIVAR_MIN_DELAY_SECONDS': os.getenv('DIVAR_MIN_DELAY_SECONDS', '20'),
        'DIVAR_MAX_DELAY_SECONDS': os.getenv('DIVAR_MAX_DELAY_SECONDS', '60'),
        'DIVAR_PROFILE_DIR': os.getenv('DIVAR_PROFILE_DIR', str(DIVAR_PROFILE_DIR)),
        'DIVAR_PROFILE_COUNT': os.getenv('DIVAR_PROFILE_COUNT', '5'),
        'HTTP_PROXY': os.getenv('HTTP_PROXY', ''),
        'DEEPSEEK_API_KEY': _mask_secret(os.getenv('DEEPSEEK_API_KEY', '')),
        'AFRA_API_URL': os.getenv('AFRA_API_URL') or os.getenv('AFRAKALA_API_URL', 'http://192.168.170.8:8000'),
    }


@app.post('/api/divar/config')
def divar_config_save(body: dict):
    updates = {
        'DIVAR_MAX_ADS_PER_RUN': str(body.get('DIVAR_MAX_ADS_PER_RUN', os.getenv('DIVAR_MAX_ADS_PER_RUN', '200'))),
        'DIVAR_DAILY_MESSAGE_LIMIT': str(body.get('DIVAR_DAILY_MESSAGE_LIMIT', os.getenv('DIVAR_DAILY_MESSAGE_LIMIT', '30'))),
        'DIVAR_MIN_DELAY_SECONDS': str(body.get('DIVAR_MIN_DELAY_SECONDS', os.getenv('DIVAR_MIN_DELAY_SECONDS', '20'))),
        'DIVAR_MAX_DELAY_SECONDS': str(body.get('DIVAR_MAX_DELAY_SECONDS', os.getenv('DIVAR_MAX_DELAY_SECONDS', '60'))),
        'DIVAR_PROFILE_DIR': str(body.get('DIVAR_PROFILE_DIR', os.getenv('DIVAR_PROFILE_DIR', str(DIVAR_PROFILE_DIR)))),
        'DIVAR_PROFILE_COUNT': str(body.get('DIVAR_PROFILE_COUNT', os.getenv('DIVAR_PROFILE_COUNT', '5'))),
        'HTTP_PROXY': str(body.get('HTTP_PROXY', os.getenv('HTTP_PROXY', ''))),
        'DEEPSEEK_API_KEY': str(body.get('DEEPSEEK_API_KEY', os.getenv('DEEPSEEK_API_KEY', ''))),
        'AFRA_API_URL': str(body.get('AFRA_API_URL', os.getenv('AFRA_API_URL') or os.getenv('AFRAKALA_API_URL', 'http://192.168.170.8:8000'))),
    }
    _write_env_file(DIVAR_ENV_PATH, updates)
    for key, value in updates.items():
        os.environ[key] = value
    return {'saved': True, 'config': updates}


@app.get('/api/divar/template')
def divar_template():
    return {'template': load_template(str(DIVAR_ENV_PATH.parent / 'data' / 'message_template.txt'))}


@app.post('/api/divar/template')
def divar_template_save(body: dict):
    template = str(body.get('template', ''))
    path = save_template(template, str(DIVAR_ENV_PATH.parent / 'data' / 'message_template.txt'))
    return {'saved': True, 'path': path}


@app.get('/api/divar/ai/stats')
def divar_ai_stats():
    if not DIVAR_DB_PATH.exists():
        return {'total': 0, 'analyzed': 0, 'pending': 0, 'failed': 0}
    conn = divar_db()
    total = conn.execute("SELECT COUNT(*) FROM divar_leads").fetchone()[0]
    analyzed = conn.execute("SELECT COUNT(*) FROM divar_leads WHERE ai_analyzed=1").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM divar_leads WHERE ai_analyzed=0 AND extraction_status='ok'").fetchone()[0]
    failed = conn.execute("SELECT COUNT(*) FROM divar_leads WHERE extraction_status='failed'").fetchone()[0]
    conn.close()
    return {'total': total, 'analyzed': analyzed, 'pending': pending, 'failed': failed}


@app.post('/api/divar/ai/run')
def divar_ai_run():
    conn = divar_db()
    rows = conn.execute("""
        SELECT id, title, price_text, description, city, seller_name
        FROM divar_leads
        WHERE ai_analyzed = 0 AND extraction_status = 'ok'
    """).fetchall()
    conn.close()
    analyzer = DeepSeekAnalyzer()
    analyzed = 0
    for row in rows:
        lead_id = row[0]
        lead = {'id': lead_id, 'title': row[1], 'price_text': row[2], 'description': row[3], 'city': row[4], 'seller_name': row[5]}
        analysis = analyzer.analyze(lead)
        if analysis:
            conn = divar_db()
            conn.execute('UPDATE divar_leads SET ai_analysis=?, ai_analyzed=1 WHERE id=?', (analysis, lead_id))
            conn.commit()
            conn.close()
            analyzed += 1
    return {'started': True, 'analyzed': analyzed}


@app.get('/api/divar/export')
def divar_export():
    export_dir = BASE_DIR / 'output' / 'divar'
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = export_to_excel(str(DIVAR_DB_PATH), str(export_dir))
    return FileResponse(output_path, filename=Path(output_path).name)


@app.get('/api/divar/exports')
def divar_exports():
    export_dir = BASE_DIR / 'output' / 'divar'
    if not export_dir.exists():
        return {'items': []}
    items = []
    for path in sorted(export_dir.glob('*.xlsx'), key=lambda p: p.stat().st_mtime, reverse=True):
        items.append({'name': path.name, 'size': path.stat().st_size, 'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(path.stat().st_mtime))})
    return {'items': items}

# ─── Torob API ───────────────────────────────────────────────
TOROB_DB_PATH  = BASE_DIR / 'data' / 'torob.db'
TOROB_LOG_PATH = BASE_DIR / 'logs' / 'torob_bot.log'
TOROB_RUN_PY   = BASE_DIR / 'torob-bot' / 'run.py'
TOROB_ENV_PATH = BASE_DIR / 'torob-bot' / '.env'
TOROB_RUN_PROCESS: subprocess.Popen | None = None


def torob_db():
    return sqlite3.connect(str(TOROB_DB_PATH))


@app.get('/api/torob/config')
def torob_config():
    return {
        'AFRA_API_URL': os.getenv('AFRA_API_URL') or os.getenv('AFRAKALA_API_URL', 'http://192.168.170.8:8000'),
        'AFRA_API_KEY': _mask_secret(os.getenv('AFRA_API_KEY') or os.getenv('AFRAKALA_API_KEY', '')),
        'TOROB_MIN_DELAY_SECONDS': os.getenv('TOROB_MIN_DELAY_SECONDS', '3'),
        'TOROB_MAX_DELAY_SECONDS': os.getenv('TOROB_MAX_DELAY_SECONDS', '8'),
        'TOROB_MAX_SELLERS_PER_URL': os.getenv('TOROB_MAX_SELLERS_PER_URL', '30'),
        'SELLER_CRAWL_TIMEOUT_SECONDS': os.getenv('SELLER_CRAWL_TIMEOUT_SECONDS', '15'),
        'CRAWL_SELLER_SITES': os.getenv('CRAWL_SELLER_SITES', 'true'),
    }


@app.post('/api/torob/config')
def torob_config_save(body: dict):
    updates = {
        'AFRA_API_URL': str(body.get('AFRA_API_URL', os.getenv('AFRA_API_URL') or os.getenv('AFRAKALA_API_URL', 'http://192.168.170.8:8000'))),
        'AFRA_API_KEY': str(body.get('AFRA_API_KEY', os.getenv('AFRA_API_KEY') or os.getenv('AFRAKALA_API_KEY', ''))),
        'TOROB_MIN_DELAY_SECONDS': str(body.get('TOROB_MIN_DELAY_SECONDS', os.getenv('TOROB_MIN_DELAY_SECONDS', '3'))),
        'TOROB_MAX_DELAY_SECONDS': str(body.get('TOROB_MAX_DELAY_SECONDS', os.getenv('TOROB_MAX_DELAY_SECONDS', '8'))),
        'TOROB_MAX_SELLERS_PER_URL': str(body.get('TOROB_MAX_SELLERS_PER_URL', os.getenv('TOROB_MAX_SELLERS_PER_URL', '30'))),
        'SELLER_CRAWL_TIMEOUT_SECONDS': str(body.get('SELLER_CRAWL_TIMEOUT_SECONDS', os.getenv('SELLER_CRAWL_TIMEOUT_SECONDS', '15'))),
        'CRAWL_SELLER_SITES': str(body.get('CRAWL_SELLER_SITES', os.getenv('CRAWL_SELLER_SITES', 'true'))),
    }
    _write_env_file(TOROB_ENV_PATH, updates)
    for key, value in updates.items():
        os.environ[key] = value
    return {'saved': True, 'config': updates}


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
def torob_sellers(limit: int = 50, offset: int = 0, crawl_status: str | None = None, sync_status: str | None = None):
    if not TOROB_DB_PATH.exists():
        return {"items": [], "total": 0}
    clauses = []
    params: list[object] = []
    if crawl_status:
        clauses.append('crawl_status = ?')
        params.append(crawl_status)
    if sync_status:
        clauses.append('sync_status = ?')
        params.append(sync_status)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    conn = torob_db()
    total = conn.execute(f"SELECT COUNT(*) FROM seller_leads{where}", params).fetchone()[0]
    rows  = conn.execute(f"""
        SELECT id, store_name, phone, email, store_url, torob_url,
               price_on_torob, instagram, telegram, whatsapp,
               crawl_status, sync_status, created_at
        FROM seller_leads{where}
        ORDER BY id DESC LIMIT ? OFFSET ?
    """, [*params, limit, offset]).fetchall()
    conn.close()
    keys = ["id","store_name","phone","email","store_url","torob_url",
            "price_on_torob","instagram","telegram","whatsapp",
            "crawl_status","sync_status","created_at"]
    return {"items": [dict(zip(keys, r)) for r in rows], "total": total}


@app.get('/api/torob/sellers/{seller_id}')
def torob_seller_detail(seller_id: int):
    if not TOROB_DB_PATH.exists():
        raise HTTPException(status_code=404, detail='seller not found')
    conn = torob_db()
    row = conn.execute("""
        SELECT id, store_name, phone, email, store_url, torob_url,
               price_on_torob, instagram, telegram, whatsapp,
               crawl_status, sync_status, created_at
        FROM seller_leads WHERE id = ?
    """, (seller_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail='seller not found')
    keys = ["id","store_name","phone","email","store_url","torob_url",
            "price_on_torob","instagram","telegram","whatsapp",
            "crawl_status","sync_status","created_at"]
    return dict(zip(keys, row))


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


@app.get('/api/torob/run/status')
def torob_run_status():
    global TOROB_RUN_PROCESS
    if not TOROB_RUN_PROCESS:
        return {'running': False, 'pid': None}
    running = TOROB_RUN_PROCESS.poll() is None
    return {'running': running, 'pid': TOROB_RUN_PROCESS.pid}


@app.post('/api/torob/run/stop')
def torob_run_stop():
    global TOROB_RUN_PROCESS
    if TOROB_RUN_PROCESS and TOROB_RUN_PROCESS.poll() is None:
        TOROB_RUN_PROCESS.terminate()
        try:
            TOROB_RUN_PROCESS.wait(timeout=5)
        except Exception:
            TOROB_RUN_PROCESS.kill()
    TOROB_RUN_PROCESS = None
    return {'stopped': True}


@app.post('/api/torob/run')
def torob_run(body: dict, x_panel_password: str | None = Header(default=None)):
    require_admin(x_panel_password)
    query = body.get('query', '')
    if not query:
        raise HTTPException(status_code=400, detail='query الزامی است')
    cmd = [sys.executable, str(TOROB_RUN_PY), query]
    try:
        global TOROB_RUN_PROCESS
        TOROB_RUN_PROCESS = subprocess.Popen(cmd, cwd=str(TOROB_RUN_PY.parent), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return {'started': True, 'pid': TOROB_RUN_PROCESS.pid, 'cmd': ' '.join(cmd)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get('/api/torob/export')
def torob_export():
    export_dir = BASE_DIR / 'output' / 'torob'
    export_dir.mkdir(parents=True, exist_ok=True)
    from app.excel_exporter import ExcelExporter
    if not TOROB_DB_PATH.exists():
        raise HTTPException(status_code=404, detail='no torob database')
    conn = torob_db()
    rows = conn.execute('SELECT store_name, phone, email, store_url, instagram, telegram, whatsapp, price_on_torob, torob_url FROM seller_leads ORDER BY id DESC').fetchall()
    conn.close()
    leads = []
    for row in rows:
        leads.append({
            'store_name': row[0],
            'phone': row[1],
            'email': row[2],
            'store_url': row[3],
            'instagram': row[4],
            'telegram': row[5],
            'whatsapp': row[6],
            'price_on_torob': row[7],
            'torob_url': row[8],
        })
    exporter = ExcelExporter()
    path = exporter.export(leads)
    return FileResponse(path, filename=Path(path).name)


@app.get('/api/torob/exports')
def torob_exports():
    export_dir = BASE_DIR / 'output' / 'torob'
    if not export_dir.exists():
        return {'items': []}
    items = []
    for path in sorted(export_dir.glob('*.xlsx'), key=lambda p: p.stat().st_mtime, reverse=True):
        items.append({'name': path.name, 'size': path.stat().st_size, 'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(path.stat().st_mtime))})
    return {'items': items}
