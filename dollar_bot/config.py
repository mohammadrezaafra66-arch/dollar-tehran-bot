from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        out = value
        for key, val in os.environ.items():
            out = out.replace("${" + key + "}", val)
        return out
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    return value


def load_config(config_path: str | None = None) -> dict[str, Any]:
    load_dotenv(BASE_DIR / ".env")
    path = Path(config_path) if config_path else BASE_DIR / "config.yaml"
    if not path.exists():
        example = BASE_DIR / "config.example.yaml"
        raise FileNotFoundError(
            f"config.yaml not found. Copy {example} to {path} and edit sources."
        )

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data = _expand_env(data)

    data.setdefault("app", {})
    data.setdefault("sources", [])
    data.setdefault("sync", {})
    data.setdefault("schedule", {})

    sqlite_path = Path(data["app"].get("sqlite_path", "data/dollar_prices.db"))
    if not sqlite_path.is_absolute():
        sqlite_path = BASE_DIR / sqlite_path
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    data["app"]["sqlite_path"] = str(sqlite_path)

    export_dir = Path(data["app"].get("export_dir", "output"))
    if not export_dir.is_absolute():
        export_dir = BASE_DIR / export_dir
    export_dir.mkdir(parents=True, exist_ok=True)
    data["app"]["export_dir"] = str(export_dir)

    return data
