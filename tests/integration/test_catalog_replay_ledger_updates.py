from __future__ import annotations

from pathlib import Path


def test_catalog_backed_replay_master_reconciliation_is_recorded_in_ledgers() -> None:
    ledgers = {name: Path(name).read_text() for name in ("structure.md", "findings.md", "handguard.md")}

    for text in ledgers.values():
        assert "Master reconciliation — catalog-backed Nautilus replay" in text
        assert "catalog_backed_replay_smoke" in text
        assert "synthetic historical quote ticks" in text
        assert "not full trading-production readiness" in text

    assert "CATALOG_BACKED_REPLAY_SMOKE_MODE" in ledgers["handguard.md"]
