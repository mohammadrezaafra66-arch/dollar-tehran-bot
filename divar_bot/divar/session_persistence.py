"""Session persistence for Divar browser profiles.

This module manages durable browser profile directories for Divar workers. It is
separate from the browser pool so profile allocation, reputation, and lifecycle
can evolve without changing extraction logic.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DivarSessionProfile:
    """A durable browser session profile."""

    profile_id: str
    profile_path: Path
    reputation_score: float = 1.0
    failure_count: int = 0
    success_count: int = 0
    cooldown_until: float = 0.0
    last_used_at: float = 0.0

    @property
    def available(self) -> bool:
        """Return whether this profile is eligible for use."""

        return time.time() >= self.cooldown_until and self.reputation_score > 0.15

    def to_json(self) -> Dict[str, object]:
        """Serialize profile metadata."""

        data = asdict(self)
        data["profile_path"] = str(self.profile_path)
        return data


class DivarSessionPersistenceManager:
    """Allocates and tracks durable Divar browser profiles."""

    def __init__(self, base_dir: Optional[Path] = None, profile_count: Optional[int] = None) -> None:
        self.base_dir = base_dir or Path(os.getenv("DIVAR_PROFILE_BASE_DIR", "runtime/profiles/divar"))
        self.profile_count = profile_count or int(os.getenv("DIVAR_PROFILE_COUNT", "5"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._profiles = self._load_or_create_profiles()

    def allocate(self) -> Optional[DivarSessionProfile]:
        """Allocate the best available profile."""

        available = [profile for profile in self._profiles if profile.available]
        if not available:
            return None

        selected = sorted(available, key=lambda item: (-item.reputation_score, item.last_used_at))[0]
        selected.last_used_at = time.time()
        self._save_metadata(selected)
        return selected

    def report_success(self, profile_id: str) -> None:
        """Increase profile reputation after a successful session."""

        profile = self._find(profile_id)
        if not profile:
            return
        profile.success_count += 1
        profile.reputation_score = min(1.0, profile.reputation_score + 0.05)
        self._save_metadata(profile)

    def report_failure(self, profile_id: str, cooldown_seconds: float = 600.0) -> None:
        """Decrease profile reputation and apply cooldown."""

        profile = self._find(profile_id)
        if not profile:
            return
        profile.failure_count += 1
        profile.reputation_score = max(0.0, profile.reputation_score - 0.2)
        profile.cooldown_until = time.time() + max(0.0, cooldown_seconds)
        self._save_metadata(profile)

    def snapshot(self) -> List[Dict[str, object]]:
        """Return operational profile snapshot."""

        return [profile.to_json() | {"available": profile.available} for profile in self._profiles]

    def _load_or_create_profiles(self) -> List[DivarSessionProfile]:
        profiles: List[DivarSessionProfile] = []
        for index in range(self.profile_count):
            profile_id = f"divar-profile-{index + 1}"
            profile_path = self.base_dir / profile_id
            profile_path.mkdir(parents=True, exist_ok=True)
            metadata_path = profile_path / "metadata.json"
            if metadata_path.exists():
                try:
                    data = json.loads(metadata_path.read_text(encoding="utf-8"))
                    profiles.append(
                        DivarSessionProfile(
                            profile_id=profile_id,
                            profile_path=profile_path,
                            reputation_score=float(data.get("reputation_score", 1.0)),
                            failure_count=int(data.get("failure_count", 0)),
                            success_count=int(data.get("success_count", 0)),
                            cooldown_until=float(data.get("cooldown_until", 0.0)),
                            last_used_at=float(data.get("last_used_at", 0.0)),
                        )
                    )
                    continue
                except Exception:
                    pass
            profile = DivarSessionProfile(profile_id=profile_id, profile_path=profile_path)
            profiles.append(profile)
            self._save_metadata(profile)
        return profiles

    def _save_metadata(self, profile: DivarSessionProfile) -> None:
        metadata_path = profile.profile_path / "metadata.json"
        metadata_path.write_text(json.dumps(profile.to_json(), ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")

    def _find(self, profile_id: str) -> Optional[DivarSessionProfile]:
        for profile in self._profiles:
            if profile.profile_id == profile_id:
                return profile
        return None
