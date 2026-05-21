from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .core import extract_source, load_config


def check_sources(config_path: str = "configs/indicators.json", include_disabled: bool = True, indicator_code: str | None = None, source_code: str | None = None) -> list[dict[str, Any]]:
    config = load_config(config_path)
    app = config.get("app", {})
    rows: list[dict[str, Any]] = []
    for indicator in config.get("indicators", []):
        if indicator_code and indicator.get("code") != indicator_code:
            continue
        for source in indicator.get("sources", []):
            if source_code and source.get("code") != source_code:
                continue
            if not include_disabled and not source.get("enabled", True):
                continue
            result = extract_source(indicator, source, app)
            rows.append({
                "indicator_code": indicator.get("code"),
                "indicator_name": indicator.get("name"),
                "source_code": source.get("code"),
                "source_name": source.get("name"),
                "enabled": bool(source.get("enabled", True)),
                "price_kind": source.get("price_kind"),
                "unit": source.get("unit"),
                "ok": result.ok,
                "value_toman": result.value_toman,
                "raw_value": result.raw_value,
                "latency_ms": result.latency_ms,
                "error": result.error,
            })
    return rows


def save_report(rows: list[dict[str, Any]], output_path: str = "output/source_check_report.json") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def enable_successful_pending(config_path: str = "configs/indicators.json", indicator_code: str | None = None, source_code: str | None = None, min_value: int = 1) -> dict[str, Any]:
    rows = check_sources(config_path=config_path, include_disabled=True, indicator_code=indicator_code, source_code=source_code)
    pending_rows = [row for row in rows if not row.get("enabled")]
    report_path = save_report(pending_rows)
    passed = set()
    for row in pending_rows:
        value = row.get("value_toman")
        if row.get("ok") and isinstance(value, int) and value >= min_value and row.get("raw_value"):
            passed.add(row.get("source_code"))

    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = Path("output/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / ("indicators-before-enable-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
    backup_path.write_text(config_file.read_text(encoding="utf-8"), encoding="utf-8")

    config = load_config(config_path)
    enabled_codes = []
    for indicator in config.get("indicators", []):
        for source in indicator.get("sources", []):
            if source.get("code") in passed and not source.get("enabled", True):
                source["enabled"] = True
                source["notes"] = "Enabled automatically after successful local source check."
                enabled_codes.append(source.get("code"))

    config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "checked_pending": len(pending_rows),
        "enabled_count": len(enabled_codes),
        "enabled_sources": enabled_codes,
        "report": report_path,
        "backup": str(backup_path),
    }
