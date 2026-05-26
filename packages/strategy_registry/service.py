from __future__ import annotations

from .models import ExternalStrategyClassification, ExternalStrategyEntry, ImportedDraft, StrategyModuleEntry


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


_ALLOWED_MODULE_PREFIXES = (
    "packages.nautilus_rule_graph.",
)


class StrategyModuleRegistryService:
    """Metadata-only registry for StrategySpec-derived Nautilus strategy modules.

    The registry deliberately does not import the target modules. It only returns
    allowlisted metadata that a separate compiler/backtest boundary may use.
    """

    def __init__(self) -> None:
        self._modules: dict[str, StrategyModuleEntry] = {}
        self.register_safe_module(
            module_id="rule_graph_backtest",
            strategy_class_path="packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategy",
            config_class_path="packages.nautilus_rule_graph.config:RuleGraphStrategyConfig",
            input_kind="strategy_spec",
        )

    def register_safe_module(
        self,
        *,
        module_id: str,
        strategy_class_path: str,
        config_class_path: str,
        input_kind: str = "strategy_spec",
    ) -> StrategyModuleEntry:
        self._validate_module_path(strategy_class_path)
        self._validate_module_path(config_class_path)
        entry = StrategyModuleEntry(
            module_id=module_id,
            strategy_class_path=strategy_class_path,
            config_class_path=config_class_path,
            input_kind=input_kind,
            read_only=True,
            execution_authority=False,
            live_trading_enabled=False,
            credentials_required=False,
            resolution_mode="metadata_only",
        )
        self._modules[module_id] = entry
        return entry

    def list_modules(self) -> list[StrategyModuleEntry]:
        return list(self._modules.values())

    def select_for_strategy_spec(self, module_id: str = "rule_graph_backtest") -> StrategyModuleEntry:
        try:
            entry = self._modules[module_id]
        except KeyError as exc:
            raise ValueError(f"unknown strategy module: {module_id}") from exc
        if entry.input_kind != "strategy_spec":
            raise ValueError(f"strategy module is not StrategySpec-compatible: {module_id}")
        return entry

    @staticmethod
    def _validate_module_path(module_path: str) -> None:
        module_name, separator, attribute = module_path.partition(":")
        if not separator or not module_name or not attribute:
            raise ValueError("module path must use module:attribute form")
        if not any(module_name.startswith(prefix) for prefix in _ALLOWED_MODULE_PREFIXES):
            raise ValueError("module path is not allowlisted")
