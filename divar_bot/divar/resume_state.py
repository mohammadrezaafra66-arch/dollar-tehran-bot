"""Pipeline resume state manager.

This module allows Divar extraction runs to continue after crashes or restarts.
The resume state is intentionally durable and database-backed instead of relying
only on in-memory orchestration state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from divar_bot.divar.storage import DivarStorage


@dataclass(frozen=True)
class DivarResumeSnapshot:
    """Serializable resume snapshot for one pipeline run."""

    run_id: str
    listing_url: str
    pending_ads: List[Dict[str, Any]]
    completed_ads: int
    failed_ads: int


class DivarResumeManager:
    """Provides durable resume snapshots for interrupted runs."""

    def __init__(self, storage: Optional[DivarStorage] = None) -> None:
        self.storage = storage or DivarStorage()

    def snapshot(self, run_id: str, listing_url: str) -> DivarResumeSnapshot:
        """Build a resume snapshot from persistent storage."""

        pending = self.storage.pending_ads(run_id)

        completed = 0
        failed = 0
        with self.storage.connect() as conn:
            completed = int(
                conn.execute(
                    "SELECT COUNT(*) FROM divar_discovered_ads WHERE run_id=? AND status='done'",
                    (run_id,),
                ).fetchone()[0]
            )
            failed = int(
                conn.execute(
                    "SELECT COUNT(*) FROM divar_discovered_ads WHERE run_id=? AND status='failed'",
                    (run_id,),
                ).fetchone()[0]
            )

        return DivarResumeSnapshot(
            run_id=run_id,
            listing_url=listing_url,
            pending_ads=pending,
            completed_ads=completed,
            failed_ads=failed,
        )

    def should_resume(self, run_id: str) -> bool:
        """Return whether a run still has unfinished ads."""

        return len(self.storage.pending_ads(run_id)) > 0

    def restore_pending_ads(self, run_id: str) -> List[Dict[str, Any]]:
        """Return ads that still require processing."""

        return self.storage.pending_ads(run_id)
