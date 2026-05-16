from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        out = value
        for key, val in os.environ.items():
            out = out.replace('${' + key + '}', val)
        return out
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    return value


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in ('true', 'True'):
        return True
    if value in ('false', 'False'):
        return False
    if value in ('null', 'None', ''):
        return None if value in ('null', 'None') else ''
    try:
        return ast.literal_eval(value)
    except Exception:
        return value.strip('"').strip("'")


def _mini_yaml(text: str) -> dict[str, Any]:
    # Parser کوچک برای config.example.yaml همین پروژه؛ جایگزین PyYAML برای نصب سبک روی ویندوز.
    root: dict[str, Any] = {}
    current_section: str | None = None
    current_item: dict[str, Any] | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        indent = len(raw) - len(raw.lstrip(' '))
        line = raw.strip()
        if indent == 0 and line.endswith(':'):
            current_section = line[:-1]
            root[current_section] = [] if current_section == 'sources' else {}
            current_item = None
            continue
        if current_section is None:
            continue
        if current_section == 'sources':
            if line.startswith('- '):
                current_item = {}
                root['sources'].append(current_item)
                rest = line[2:].strip()
                if rest and ':' in rest:
                    k, v = rest.split(':', 1)
                    current_item[k.strip()] = _parse_scalar(v)
            elif current_item is not None and ':' in line:
                k, v = line.split(':', 1)
                current_item[k.strip()] = _parse_scalar(v)
        else:
            if ':' in line:
                k, v = line.split(':', 1)
                root[current_section][k.strip()] = _parse_scalar(v)
    return root


def load_config(config_path: str | None = None) -> dict[str, Any]:
    _load_env_file(BASE_DIR / '.env')
    path = Path(config_path) if config_path else BASE_DIR / 'config.yaml'
    if not path.exists():
        example = BASE_DIR / 'config.example.yaml'
        raise FileNotFoundError(f'config.yaml not found. Copy {example} to {path} and edit sources.')

    data = _mini_yaml(path.read_text(encoding='utf-8'))
    data = _expand_env(data)

    data.setdefault('app', {})
    data.setdefault('sources', [])
    data.setdefault('sync', {})
    data.setdefault('schedule', {})

    sqlite_path = Path(data['app'].get('sqlite_path', 'data/dollar_prices.db'))
    if not sqlite_path.is_absolute():
        sqlite_path = BASE_DIR / sqlite_path
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    data['app']['sqlite_path'] = str(sqlite_path)

    export_dir = Path(data['app'].get('export_dir', 'output'))
    if not export_dir.is_absolute():
        export_dir = BASE_DIR / export_dir
    export_dir.mkdir(parents=True, exist_ok=True)
    data['app']['export_dir'] = str(export_dir)

    return data
