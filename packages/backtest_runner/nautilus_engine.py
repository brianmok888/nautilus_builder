from __future__ import annotations

from typing import Protocol

from packages.backtest_runner.config_builder import build_backtest_config
from packages.backtest_runner.result_normalizer import normalize_backtest_result
from packages.backtest_runner.artifacts import BacktestResultArtifact


class BacktestEngineProtocol(Protocol):
    def run(self, config: dict[str, object]) -> dict[str, object]: ...


class NautilusBacktestEngineBoundary:
    def __init__(self, *, engine: BacktestEngineProtocol) -> None:
        self._engine = engine

    def run(
        self,
        *,
        backtest_job_id: str,
        strategy_spec_version: str,
        adapter_id: str,
        instrument_id: str,
        compile_hash: str,
        validation_report_id: str,
        worker_image: str,
    ) -> BacktestResultArtifact:
        config = build_backtest_config(
            strategy_spec_version=strategy_spec_version,
            adapter_id=adapter_id,
            instrument_id=instrument_id,
            compile_hash=compile_hash,
            validation_report_id=validation_report_id,
            worker_image=worker_image,
        )
        raw_result = self._engine.run(config)
        return normalize_backtest_result(
            raw_result=raw_result,
            backtest_job_id=backtest_job_id,
            strategy_spec_version=strategy_spec_version,
            compile_hash=compile_hash,
            worker_image=worker_image,
        )
