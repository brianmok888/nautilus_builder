from __future__ import annotations

import pytest

from packages.strategy_registry.service import StrategyRegistryService


def test_safe_import_creates_new_draft_strategy_spec() -> None:
    service = StrategyRegistryService()

    imported = service.import_as_draft("liquidation_cascade_reversal")

    assert imported.stage == "draft"
    assert imported.status == "imported"
    assert imported.version == "0.1.0-draft.1"
    assert imported.source_ref == "liquidation_cascade_reversal"
    assert imported.live_ready is False


def test_incompatible_source_remains_catalog_only() -> None:
    service = StrategyRegistryService()

    with pytest.raises(ValueError, match="catalog-only"):
        service.import_as_draft("unknown_python_strategy")
