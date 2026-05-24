"""Write-ahead log and snapshot recovery for Afra Automation runtime.

This module provides a durable local recovery layer for bot instances. It is not
intended to replace Kafka or the database. Instead, it protects the runtime from
process crashes between receiving a job and committing durable state.

Design goals:
- append-only WAL records with checksums
- deterministic replay
- snapshot creation and loading
- config-driven paths for Kubernetes persistent volumes
- corruption detection without crashing the whole runtime
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional


Payload = Dict[str, Any]


@dataclass(frozen=True)
class WalSettings:
    """Configuration for WAL and snapshot storage."""

    wal_path: Path
    snapshot_path: Path
    fsync: bool = True

    @classmethod
    def from_env(cls) -> "WalSettings":
        """Build settings from environment variables."""

        state_dir = Path(os.getenv("AFRA_STATE_DIR", "/var/lib/afra-runtime"))
        return cls(
            wal_path=Path(os.getenv("AFRA_WAL_PATH", str(state_dir / "runtime.wal.jsonl"))),
            snapshot_path=Path(os.getenv("AFRA_SNAPSHOT_PATH", str(state_dir / "snapshot.json"))),
            fsync=os.getenv("AFRA_WAL_FSYNC", "true").lower() == "true",
        )


@dataclass(frozen=True)
class WalRecord:
    """Single append-only WAL record."""

    event_id: str
    event_type: str
    payload: Payload
    trace_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    checksum: str = ""

    def without_checksum(self) -> Dict[str, Any]:
        """Return serializable record data without checksum."""

        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "trace_id": self.trace_id,
            "created_at": self.created_at,
        }

    def compute_checksum(self) -> str:
        """Compute SHA-256 checksum for deterministic corruption detection."""

        raw = json.dumps(self.without_checksum(), sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def sealed(self) -> "WalRecord":
        """Return the same record with checksum populated."""

        return WalRecord(
            event_id=self.event_id,
            event_type=self.event_type,
            payload=self.payload,
            trace_id=self.trace_id,
            created_at=self.created_at,
            checksum=self.compute_checksum(),
        )

    def to_json_line(self) -> str:
        """Serialize record to a JSONL line."""

        sealed = self.sealed()
        return json.dumps(
            {**sealed.without_checksum(), "checksum": sealed.checksum},
            ensure_ascii=False,
            sort_keys=True,
        )

    @classmethod
    def from_json_line(cls, line: str) -> "WalRecord":
        """Parse a WAL record from JSONL."""

        data = json.loads(line)
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            payload=data.get("payload", {}),
            trace_id=data.get("trace_id", ""),
            created_at=data.get("created_at", ""),
            checksum=data.get("checksum", ""),
        )

    def is_valid(self) -> bool:
        """Validate the record checksum."""

        return bool(self.checksum) and self.compute_checksum() == self.checksum


class WalRecovery:
    """Append-only WAL writer and deterministic replay reader."""

    def __init__(self, settings: Optional[WalSettings] = None) -> None:
        self.settings = settings or WalSettings.from_env()
        self.settings.wal_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: WalRecord) -> None:
        """Append a record and optionally fsync it to disk."""

        with self.settings.wal_path.open("a", encoding="utf-8") as file:
            file.write(record.to_json_line() + "\n")
            file.flush()
            if self.settings.fsync:
                os.fsync(file.fileno())

    def replay(self, stop_on_corruption: bool = False) -> Iterator[WalRecord]:
        """Replay valid WAL records in order.

        Corrupt records are skipped by default so one bad line does not take down
        the whole runtime. Set stop_on_corruption=True for strict recovery tests.
        """

        if not self.settings.wal_path.exists():
            return iter(())

        def _iterator() -> Iterator[WalRecord]:
            with self.settings.wal_path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = WalRecord.from_json_line(line)
                        if not record.is_valid():
                            raise ValueError(f"invalid_checksum line={line_number}")
                        yield record
                    except Exception:
                        if stop_on_corruption:
                            raise
                        continue

        return _iterator()

    def create_snapshot(self, state: Payload) -> None:
        """Atomically write a runtime snapshot."""

        snapshot = {
            "created_at": datetime.utcnow().isoformat(),
            "state": state,
            "checksum": self._checksum_payload(state),
        }
        self.settings.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(self.settings.snapshot_path.parent),
            delete=False,
        ) as tmp:
            json.dump(snapshot, tmp, ensure_ascii=False, sort_keys=True, indent=2)
            tmp.flush()
            if self.settings.fsync:
                os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)

        tmp_path.replace(self.settings.snapshot_path)

    def load_snapshot(self) -> Optional[Payload]:
        """Load a snapshot if it exists and passes checksum validation."""

        if not self.settings.snapshot_path.exists():
            return None

        with self.settings.snapshot_path.open("r", encoding="utf-8") as file:
            snapshot = json.load(file)

        state = snapshot.get("state", {})
        checksum = snapshot.get("checksum", "")
        if checksum != self._checksum_payload(state):
            return None
        return state

    def compact(self, state: Payload) -> None:
        """Create a snapshot and rotate the WAL."""

        self.create_snapshot(state)
        if self.settings.wal_path.exists():
            rotated = self.settings.wal_path.with_suffix(f".wal.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.bak")
            self.settings.wal_path.replace(rotated)

    def recover_state(self) -> Payload:
        """Recover state by loading snapshot and replaying WAL records."""

        state = self.load_snapshot() or {}
        applied: List[str] = state.setdefault("applied_events", [])

        for record in self.replay():
            if record.event_id in applied:
                continue
            state[record.event_id] = record.payload
            applied.append(record.event_id)

        return state

    def _checksum_payload(self, payload: Payload) -> str:
        """Return stable checksum for a payload."""

        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
