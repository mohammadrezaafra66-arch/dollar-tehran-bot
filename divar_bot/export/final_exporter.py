"""Final lead export pipeline for Afra Automation.

This module turns normalized leads into human-readable outputs. Excel is treated
as a user-facing export format, not the source of truth. Runtime/database layers
should remain authoritative.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


@dataclass(frozen=True)
class ExportSettings:
    """Settings for final lead exports."""

    output_dir: Path
    csv_filename: str = "divar_leads_final.csv"
    jsonl_filename: str = "divar_leads_final.jsonl"

    @classmethod
    def default(cls) -> "ExportSettings":
        return cls(output_dir=Path("output"))


class FinalLeadExporter:
    """Exports final normalized leads to CSV and JSONL."""

    COLUMNS = [
        "source_platform",
        "source_url",
        "title",
        "price_text",
        "seller_name",
        "phone",
        "city",
        "district",
        "description",
        "lead_score",
        "data_quality",
        "extracted_status",
        "exported_at",
    ]

    def __init__(self, settings: Optional[ExportSettings] = None) -> None:
        self.settings = settings or ExportSettings.default()
        self.settings.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, leads: Iterable[Mapping[str, Any]]) -> Dict[str, str]:
        """Export leads to CSV and JSONL and return generated paths."""

        normalized = [self._normalize(row) for row in leads]
        csv_path = self.settings.output_dir / self.settings.csv_filename
        jsonl_path = self.settings.output_dir / self.settings.jsonl_filename

        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(normalized)

        with jsonl_path.open("w", encoding="utf-8") as file:
            for row in normalized:
                file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

        return {"csv": str(csv_path), "jsonl": str(jsonl_path)}

    def _normalize(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        exported_at = datetime.utcnow().isoformat()
        data = {column: row.get(column, "") for column in self.COLUMNS}
        data["source_platform"] = data.get("source_platform") or "divar"
        data["exported_at"] = exported_at
        data["data_quality"] = data.get("data_quality") or self._quality(data)
        data["lead_score"] = data.get("lead_score") or self._score(data)
        return data

    def _quality(self, row: Mapping[str, Any]) -> str:
        if row.get("phone") and row.get("title") and row.get("city"):
            return "high"
        if row.get("phone") or row.get("title"):
            return "medium"
        return "low"

    def _score(self, row: Mapping[str, Any]) -> int:
        score = 1
        if row.get("phone"):
            score += 4
        if row.get("title"):
            score += 2
        if row.get("city"):
            score += 1
        if row.get("price_text"):
            score += 1
        if row.get("description"):
            score += 1
        return min(score, 10)
