"""Operational reporting for Afra Automation runtime.

This module generates compact daily/runtime reports for operators. Reports are
focused on operational health and extraction productivity, not business CRM
analytics. The final Afra assistant web app can consume these summaries later
through an API or database view.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class OperationalReport:
    """Daily operational summary."""

    generated_at: str
    jobs_processed: int = 0
    jobs_failed: int = 0
    jobs_retried: int = 0
    dead_letters: int = 0
    leads_exported: int = 0
    duplicates_merged: int = 0
    browser_active_leases: int = 0
    queue_depth: int = 0
    runtime_ready: bool = True
    notes: str = ""

    @property
    def failure_rate(self) -> float:
        """Return failed/processed ratio."""

        if self.jobs_processed <= 0:
            return 0.0
        return round(self.jobs_failed / self.jobs_processed, 4)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize report with derived fields."""

        data = asdict(self)
        data["failure_rate"] = self.failure_rate
        return data


class OperationalReportGenerator:
    """Generates JSON and CSV operational reports."""

    def __init__(self, output_dir: Path | str = "reports") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def from_snapshot(self, snapshot: Mapping[str, Any], notes: str = "") -> OperationalReport:
        """Build a report from a runtime snapshot dictionary."""

        metrics = snapshot.get("metrics", {}) if isinstance(snapshot.get("metrics", {}), Mapping) else {}
        return OperationalReport(
            generated_at=datetime.utcnow().isoformat(),
            jobs_processed=int(metrics.get("jobs_processed", 0)),
            jobs_failed=int(metrics.get("jobs_failed", 0)),
            jobs_retried=int(metrics.get("jobs_retried", 0)),
            dead_letters=int(metrics.get("dead_letters_total", 0)),
            leads_exported=int(metrics.get("leads_exported", 0)),
            duplicates_merged=int(metrics.get("duplicates_merged", 0)),
            browser_active_leases=int(metrics.get("browser_active_leases", 0)),
            queue_depth=int(metrics.get("queue_depth", 0)),
            runtime_ready=bool(snapshot.get("ready", True)),
            notes=notes,
        )

    def write(self, report: OperationalReport, basename: Optional[str] = None) -> Dict[str, str]:
        """Write report as JSON and CSV."""

        safe_name = basename or datetime.utcnow().strftime("operational_report_%Y%m%d_%H%M%S")
        json_path = self.output_dir / f"{safe_name}.json"
        csv_path = self.output_dir / f"{safe_name}.csv"
        data = report.to_dict()

        json_path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")

        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=list(data.keys()))
            writer.writeheader()
            writer.writerow(data)

        return {"json": str(json_path), "csv": str(csv_path)}
