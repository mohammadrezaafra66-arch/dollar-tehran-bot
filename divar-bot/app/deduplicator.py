"""Lead deduplication engine for Afra Automation.

This module prevents duplicated leads from polluting exports, CRM syncs, and
analytics. The current implementation is conservative and deterministic.
Future versions can add fuzzy matching, embeddings, or ML-assisted clustering.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple


@dataclass(frozen=True)
class DeduplicationResult:
    """Result of a deduplication pass."""

    unique_leads: List[Dict[str, Any]]
    duplicate_count: int


class LeadDeduplicator:
    """Deterministic lead deduplication and merge engine."""

    def deduplicate(self, leads: Iterable[Mapping[str, Any]]) -> DeduplicationResult:
        """Remove duplicates and merge complementary fields."""

        grouped: Dict[str, Dict[str, Any]] = {}
        duplicates = 0

        for lead in leads:
            key = self._identity_key(lead)
            if key not in grouped:
                grouped[key] = dict(lead)
                continue

            duplicates += 1
            grouped[key] = self._merge(grouped[key], lead)

        return DeduplicationResult(
            unique_leads=list(grouped.values()),
            duplicate_count=duplicates,
        )

    def _identity_key(self, lead: Mapping[str, Any]) -> str:
        """Build deterministic identity key for one lead."""

        stable = "|".join(
            [
                str(lead.get("phone", "")).strip().lower(),
                str(lead.get("title", "")).strip().lower(),
                str(lead.get("city", "")).strip().lower(),
            ]
        )
        if stable.strip("|"):
            return hashlib.sha256(stable.encode("utf-8")).hexdigest()

        fallback = str(lead.get("source_url", "")).strip().lower()
        return hashlib.sha256(fallback.encode("utf-8")).hexdigest()

    def _merge(self, left: Mapping[str, Any], right: Mapping[str, Any]) -> Dict[str, Any]:
        """Merge two similar leads conservatively."""

        merged = dict(left)
        for key, value in right.items():
            current = merged.get(key)
            if not current and value:
                merged[key] = value
                continue

            if isinstance(current, str) and isinstance(value, str):
                if len(value) > len(current):
                    merged[key] = value

        merged["deduplicated"] = True
        return merged
