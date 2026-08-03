import os
import subprocess
from pathlib import Path
from typing import Any


class BotManager:
    """Simple process manager for the three active bots."""

    def __init__(self) -> None:
        self.processes: dict[str, subprocess.Popen[Any]] = {}
        self.bot_paths = {
            "divar": Path("divar-bot"),
            "torob": Path("torob-bot"),
            "google-maps": Path("google-maps-bot"),
        }

    async def start_bot(self, bot_name: str, params: dict[str, Any]) -> dict[str, Any]:
        bot_path = self.bot_paths.get(bot_name)
        if not bot_path:
            return {"status": "error", "message": f"ربات {bot_name} پیدا نشد"}

        cmd = [
            "python",
            str(bot_path / "driver.py"),
            "--config",
            params.get("config", "config.yaml"),
            "--input",
            params.get("input", ""),
        ]
        if params.get("output"):
            cmd.extend(["--output", params["output"]])

        process = subprocess.Popen(
            cmd,
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.processes[bot_name] = process
        return {"status": "running", "message": f"ربات {bot_name} شروع شد", "pid": process.pid}

    async def stop_bot(self, bot_name: str) -> dict[str, Any]:
        process = self.processes.get(bot_name)
        if not process:
            return {"status": "error", "message": f"ربات {bot_name} در حال اجرا نیست"}
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
        self.processes.pop(bot_name, None)
        return {"status": "stopped", "message": f"ربات {bot_name} متوقف شد"}

    async def get_status(self, bot_name: str) -> dict[str, Any]:
        process = self.processes.get(bot_name)
        if process:
            return {"status": "running", "pid": process.pid}
        return {"status": "stopped", "pid": None}

    async def get_logs(self, bot_name: str, lines: int = 100) -> dict[str, Any]:
        log_file = Path(f"logs/{bot_name}.log")
        if not log_file.exists():
            return {"logs": []}
        with log_file.open("r", encoding="utf-8", errors="replace") as handle:
            content = handle.readlines()[-lines:]
        return {"logs": content}

    async def list_exports(self, bot_name: str) -> dict[str, Any]:
        export_dir = Path(f"{bot_name}-bot/output")
        if not export_dir.exists():
            return {"files": []}
        return {"files": [item.name for item in export_dir.glob("*.xlsx")]}
