"""Chaos tests for abrupt worker termination and replay recovery."""

from __future__ import annotations

from divar_bot.infra.wal_recovery import WalRecord, WalRecovery, WalSettings


def test_worker_crash_replays_unfinished_state(tmp_path) -> None:
    """Simulate a worker crash before durable completion handling."""

    wal = WalRecovery(
        WalSettings(
            wal_path=tmp_path / "runtime.wal.jsonl",
            snapshot_path=tmp_path / "snapshot.json",
            fsync=False,
        )
    )

    wal.append(
        WalRecord(
            event_id="evt-crash-1",
            event_type="job_received",
            payload={"url": "https://example.test/divar/1"},
            trace_id="trace-crash-1",
        )
    )

    recovered = wal.recover_state()

    assert "evt-crash-1" in recovered
    assert recovered["evt-crash-1"]["url"] == "https://example.test/divar/1"
    assert "evt-crash-1" in recovered["applied_events"]


def test_corrupt_wal_line_does_not_break_recovery(tmp_path) -> None:
    """A corrupted WAL line must not crash the whole replay process."""

    settings = WalSettings(
        wal_path=tmp_path / "runtime.wal.jsonl",
        snapshot_path=tmp_path / "snapshot.json",
        fsync=False,
    )
    wal = WalRecovery(settings)

    wal.append(
        WalRecord(
            event_id="evt-valid",
            event_type="job_received",
            payload={"ok": True},
            trace_id="trace-valid",
        )
    )

    with settings.wal_path.open("a", encoding="utf-8") as file:
        file.write("{corrupted-json-line}\n")

    wal.append(
        WalRecord(
            event_id="evt-valid-2",
            event_type="job_completed",
            payload={"ok": True},
            trace_id="trace-valid-2",
        )
    )

    replayed = list(wal.replay(stop_on_corruption=False))

    assert len(replayed) == 2
    assert replayed[0].event_id == "evt-valid"
    assert replayed[1].event_id == "evt-valid-2"
