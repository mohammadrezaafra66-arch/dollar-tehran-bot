import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def _python_executable() -> str:
    import shutil

    for candidate in [sys.executable, "python3", "python"]:
        if candidate == sys.executable:
            return candidate
        if shutil.which(candidate):
            return candidate
    return "python3"


def _repo_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "panel-backend").exists():
        return cwd
    return Path(__file__).resolve().parents[3]


def _state_dir() -> Path:
    path = _repo_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path(bot_name: str) -> Path:
    return _state_dir() / f"{bot_name}_state.json"


def _bot_dir(bot_name: str) -> Path:
    return _repo_root() / f"{bot_name}-bot"


def _log_path(bot_name: str) -> Path:
    return _bot_dir(bot_name) / "logs" / f"{bot_name}.log"


def _resolve_cwd(cwd: Optional[Union[str, Path]]) -> Path:
    if cwd is None:
        return _repo_root()
    path = Path(cwd)
    if path.is_absolute():
        return path
    return _repo_root() / path


def _is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _read_log_lines(log_path: Path, lines: int) -> List[str]:
    if not log_path.exists():
        return []
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        content = handle.readlines()
    if lines <= 0:
        return []
    return content[-lines:]


def _write_state(bot_name: str, payload: Dict[str, Any]) -> None:
    path = _state_path(bot_name)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _remove_state(bot_name: str) -> None:
    path = _state_path(bot_name)
    if path.exists():
        path.unlink(missing_ok=True)


def _read_state(bot_name: str) -> Optional[Dict[str, Any]]:
    path = _state_path(bot_name)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        _remove_state(bot_name)
        return None


def start_process(
    bot_name: str,
    cmd: Union[List[str], str],
    cwd: Optional[Union[str, Path]] = None,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    if isinstance(cmd, list) and cmd and cmd[0] == "python":
        cmd = [_python_executable()] + cmd[1:]

    state = _read_state(bot_name)
    if state and state.get("running") and state.get("pid"):
        pid = int(state["pid"])
        if _is_pid_alive(pid):
            return {"started": False, "pid": pid, "cmd": state.get("cmd", cmd)}

    resolved_cwd = _resolve_cwd(cwd)
    if isinstance(cmd, str):
        command = cmd
        shell = True
    else:
        command = cmd
        shell = False

    process = subprocess.Popen(
        command,
        cwd=str(resolved_cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=shell,
    )

    payload = {
        "pid": process.pid,
        "cmd": cmd if isinstance(cmd, list) else cmd,
        "started_at": __import__("datetime").datetime.now().isoformat(),
        "running": True,
    }
    _write_state(bot_name, payload)
    return {"started": True, "pid": process.pid, "cmd": payload["cmd"]}


def stop_process(bot_name: str) -> Dict[str, Any]:
    state = _read_state(bot_name)
    pid = state.get("pid") if state else None
    if not pid:
        _remove_state(bot_name)
        return {"stopped": False}

    pid_int = int(pid)
    if _is_pid_alive(pid_int):
        try:
            os.kill(pid_int, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass

    if _is_pid_alive(pid_int):
        try:
            os.kill(pid_int, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass

    _remove_state(bot_name)
    return {"stopped": True}


def get_status(bot_name: str) -> Dict[str, Any]:
    state = _read_state(bot_name)
    pid = state.get("pid") if state else None
    if not pid:
        return {"running": False, "pid": None, "output": []}

    pid_int = int(pid)
    if not _is_pid_alive(pid_int):
        _remove_state(bot_name)
        return {"running": False, "pid": None, "output": []}

    log_path = _log_path(bot_name)
    output = _read_log_lines(log_path, 20)
    return {"running": True, "pid": pid_int, "output": output}


def get_logs(bot_name: str, lines: int = 100) -> List[str]:
    log_path = _log_path(bot_name)
    return _read_log_lines(log_path, lines)
