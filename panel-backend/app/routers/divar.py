import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Annotated, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path as FastAPIPath, Query

from ..services.config_manager import read_divar_config, read_template, write_config, write_template
from ..services.db_reader import divar_ai_stats, divar_leads, divar_send_log, divar_stats
from ..services.process_manager import _repo_root, get_logs, get_status, start_process, stop_process

router = APIRouter(prefix="/api/divar", tags=["Divar"])


@router.get("/stats")
async def get_divar_stats() -> Dict[str, Any]:
    return divar_stats()


@router.get("/leads")
async def get_divar_leads(
    limit: Annotated[int, Query()] = 100,
    offset: Annotated[int, Query()] = 0,
    status: Annotated[Optional[str], Query()] = None,
    city: Annotated[Optional[str], Query()] = None,
    message_sent: Annotated[Optional[str], Query()] = None,
) -> Dict[str, Any]:
    return divar_leads(limit=limit, offset=offset, status=status, city=city, message_sent=message_sent)


@router.get("/logs")
async def get_divar_process_logs(lines: Annotated[int, Query()] = 100) -> Dict[str, Any]:
    return {"lines": get_logs("divar", lines)}


@router.post("/run")
async def run_divar(payload: dict) -> Dict[str, Any]:
    url = str(payload.get("url", "")).strip()
    send_messages = bool(payload.get("send_messages", False))
    no_ai = bool(payload.get("no_ai", False))

    cmd = ["python", "divar-bot/driver.py", "--mode", "run", "--url", url]
    if send_messages:
        cmd.append("--send-messages")
    if no_ai:
        cmd.append("--no-ai")

    return start_process("divar", cmd)


@router.get("/run/status")
async def get_divar_run_status() -> Dict[str, Any]:
    return get_status("divar")


@router.post("/run/stop")
async def stop_divar_run() -> Dict[str, Any]:
    return stop_process("divar")


@router.get("/send-log")
async def get_divar_send_log(limit: Annotated[int, Query()] = 50) -> Dict[str, Any]:
    return {"items": divar_send_log(limit)}


@router.get("/accounts")
async def list_divar_accounts() -> Dict[str, Any]:
    profile_dir = read_divar_config().get("DIVAR_PROFILE_DIR", "")
    if not profile_dir:
        return {"items": []}

    base_path = _repo_root() / profile_dir
    if not base_path.exists() or not base_path.is_dir():
        return {"items": []}

    items = []
    for child in sorted(base_path.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        cookies_path = child / "Cookies"
        items.append(
            {
                "profile_id": child.name,
                "has_session_files": cookies_path.exists() and cookies_path.stat().st_size > 0,
                "available": True,
                "reputation_score": 0,
                "success_count": 0,
                "failure_count": 0,
                "cooldown_until": 0,
                "last_used_at": 0,
            }
        )

    return {"items": items}


@router.post("/accounts/{profile_id}/login/start")
async def start_divar_login(profile_id: Annotated[str, FastAPIPath()], payload: dict) -> Dict[str, Any]:
    phone = str(payload.get("phone", "")).strip()
    cmd = ["python", "divar-bot/driver.py", "--mode", "login", "--phone", phone]
    result = start_process(f"divar-login-{profile_id}", cmd)
    return {"started": result.get("started", False), "process_key": f"divar-login-{profile_id}"}


@router.post("/accounts/{profile_id}/login/otp")
async def submit_divar_login_otp(profile_id: Annotated[str, FastAPIPath()], payload: dict) -> Dict[str, Any]:
    otp = str(payload.get("otp", "")).strip()
    otp_path = _repo_root() / "data" / f"divar_otp_{profile_id}.txt"
    otp_path.parent.mkdir(parents=True, exist_ok=True)
    otp_path.write_text(otp, encoding="utf-8")
    return {"sent": True}


@router.get("/accounts/{profile_id}/login/status")
async def get_divar_login_status(profile_id: Annotated[str, FastAPIPath()]) -> Dict[str, Any]:
    status = get_status(f"divar-login-{profile_id}")
    return {"running": status.get("running", False), "output": status.get("output", []), "success": not status.get("running", False)}


@router.get("/accounts/{profile_id}/check-login")
async def check_divar_login(profile_id: Annotated[str, FastAPIPath()]) -> Dict[str, Any]:
    profile_dir = read_divar_config().get("DIVAR_PROFILE_DIR", "")
    cookies_path = _repo_root() / profile_dir / profile_id / "Cookies" if profile_dir else None
    if cookies_path is None:
        return {"likely_logged_in": False, "phone": "", "cookies_size": 0}

    exists = cookies_path.exists() and cookies_path.is_file()
    size = cookies_path.stat().st_size if exists else 0
    return {"likely_logged_in": exists and size > 0, "phone": "", "cookies_size": size}


@router.post("/accounts/{profile_id}/save-phone")
async def save_divar_phone(profile_id: Annotated[str, FastAPIPath()], payload: dict) -> Dict[str, Any]:
    phone = str(payload.get("phone", "")).strip()
    phone_path = _repo_root() / "data" / f"divar_phone_{profile_id}.txt"
    phone_path.parent.mkdir(parents=True, exist_ok=True)
    phone_path.write_text(phone, encoding="utf-8")
    return {"saved": True}


@router.delete("/accounts/{profile_id}")
async def delete_divar_account(profile_id: Annotated[str, FastAPIPath()]) -> Dict[str, Any]:
    profile_dir = read_divar_config().get("DIVAR_PROFILE_DIR", "")
    if not profile_dir:
        raise HTTPException(status_code=404, detail="پروفایل یافت نشد.")

    target_path = _repo_root() / profile_dir / profile_id
    if not target_path.exists() or not target_path.is_dir():
        raise HTTPException(status_code=404, detail="پروفایل یافت نشد.")

    shutil.rmtree(target_path)
    return {"deleted": True}


@router.get("/config")
async def get_divar_config() -> Dict[str, Any]:
    return read_divar_config()


@router.post("/config")
async def save_divar_config(payload: dict) -> Dict[str, Any]:
    return {"saved": write_config("divar", payload)}


@router.get("/template")
async def get_divar_template() -> Dict[str, Any]:
    return {"template": read_template()}


@router.post("/template")
async def save_divar_template(payload: dict) -> Dict[str, Any]:
    template = str(payload.get("template", ""))
    return {"saved": write_template(template)}


@router.get("/ai/stats")
async def get_divar_ai_stats() -> Dict[str, Any]:
    return divar_ai_stats()


@router.post("/ai/run")
async def run_divar_ai() -> Dict[str, Any]:
    cmd = ["python", "divar-bot/driver.py", "--mode", "sync"]
    result = start_process("divar-ai", cmd)
    return {"started": result.get("started", False)}


@router.get("/exports")
async def list_divar_exports() -> Dict[str, Any]:
    output_dir = _repo_root() / "divar-bot" / "output"
    if not output_dir.exists():
        return {"items": []}

    items = []
    for path in sorted(output_dir.glob("*.xlsx"), key=lambda item: item.name):
        stat = path.stat()
        items.append(
            {
                "name": path.name,
                "path": str(path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )
    return {"items": items}


@router.get("/export")
async def get_latest_divar_export() -> Dict[str, Any]:
    output_dir = _repo_root() / "divar-bot" / "output"
    if not output_dir.exists():
        return {"file": ""}

    files = sorted(output_dir.glob("*.xlsx"), key=lambda item: item.stat().st_mtime, reverse=True)
    return {"file": files[0].name if files else ""}
