from __future__ import annotations

from tests.strategy_spec.test_schema_valid import make_valid_spec
from services.api.app import create_app


def test_strategy_spec_can_be_saved_listed_and_read_by_api() -> None:
    app = create_app()
    payload = make_valid_spec()

    created = app.post("/api/strategies", json=payload)
    listed = app.get("/api/strategies")
    detail = app.get("/api/strategies/strategy_001")

    assert created.status_code == 201
    assert created.json()["strategy_id"] == "strategy_001"
    assert listed.json()[0]["strategy_id"] == "strategy_001"
    assert detail.json()["versions"][0]["spec"]["version"] == "0.1.0-draft.1"


def test_strategy_spec_update_and_version_preserve_lineage_identity() -> None:
    app = create_app()
    payload = make_valid_spec()

    created = app.post("/api/strategies", json=payload).json()
    updated_payload = {**payload, "version": "0.1.0-draft.2"}
    updated = app.post("/api/strategies/strategy_001/draft", json=updated_payload).json()
    versioned = app.post("/api/strategies/strategy_001/versions", json=updated_payload).json()
    detail = app.get("/api/strategies/strategy_001").json()

    assert created["strategy_lineage_id"] == "lineage_strategy_001"
    assert updated["strategy_lineage_id"] == created["strategy_lineage_id"]
    assert versioned["strategy_version_id"] == "strategy_001_v002"
    assert detail["strategy_lineage_id"] == "lineage_strategy_001"
    assert [entry["strategy_version_id"] for entry in detail["versions"]] == ["strategy_001_v001", "strategy_001_v002"]


def test_strategy_detail_frontend_pages_are_present() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    assert (root / "apps" / "web" / "app" / "strategies" / "page.tsx").exists()
    assert (root / "apps" / "web" / "app" / "strategies" / "[strategyId]" / "page.tsx").exists()
