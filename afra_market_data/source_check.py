from __future__ import annotations

import json
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
