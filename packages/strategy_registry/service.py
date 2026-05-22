from __future__ import annotations

from .models import ExternalStrategyClassification, ExternalStrategyEntry, ImportedDraft


class StrategyRegistryService:
    def __init__(self) -> None:
        self._entries = {
            "liquidation_cascade_reversal": ExternalStrategyEntry(
                strategy_id="liquidation_cascade_reversal",
                source="daedalus",
                classification=ExternalStrategyClassification.DAEDALUS_SIGNAL_STRATEGY,
                read_only=True,
                editable_in_ux=False,
                import_allowed=True,
            ),
            "unknown_python_strategy": ExternalStrategyEntry(
                strategy_id="unknown_python_strategy",
                source="nautilus",
                classification=ExternalStrategyClassification.UNKNOWN_RAW_CODE,
                read_only=True,
                editable_in_ux=False,
                import_allowed=False,
            ),
            "unsafe_executor": ExternalStrategyEntry(
                strategy_id="unsafe_executor",
                source="daedalus",
                classification=ExternalStrategyClassification.UNSAFE_EXECUTION_STRATEGY,
                read_only=True,
                editable_in_ux=False,
                import_allowed=False,
            ),
        }

    def list_external_strategies(self) -> list[ExternalStrategyEntry]:
        return list(self._entries.values())

    def get_external_strategy(self, strategy_id: str) -> ExternalStrategyEntry:
        return self._entries[strategy_id]

    def import_as_draft(self, strategy_id: str) -> ImportedDraft:
        entry = self.get_external_strategy(strategy_id)
        if not entry.import_allowed:
            raise ValueError("strategy is catalog-only and cannot be imported as draft")

        return ImportedDraft(
            stage="draft",
            status="imported",
            version="0.1.0-draft.1",
            source_ref=entry.strategy_id,
            live_ready=False,
        )
