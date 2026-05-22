from __future__ import annotations

import hashlib
import json
from typing import Any

from packages.strategy_spec.models import StrategySpec

from .artifacts import CompileArtifact


def _stable_payload_hash(payload: dict[str, Any], profile: str) -> str:
    encoded = json.dumps({"profile": profile, "payload": payload}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compile_strategy_spec(payload: dict[str, Any], *, profile: str) -> CompileArtifact:
    spec = StrategySpec.model_validate(payload)
    compile_hash = _stable_payload_hash(spec.model_dump(mode="json"), profile)

    if profile == "backtest":
        return CompileArtifact(
            profile="backtest",
            strategy_class="RuleGraphBacktestStrategy",
            output_mode="backtest_order_intent",
            execution_authority=False,
            spec_version=spec.version,
            adapter_id=spec.adapter_id,
            instrument_id=spec.instrument_id,
            compile_hash=compile_hash,
        )

    if profile == "signal_preview_only":
        return CompileArtifact(
            profile="signal_preview_only",
            strategy_class="RuleGraphSignalStrategy",
            output_mode="signal_preview_only",
            execution_authority=False,
            spec_version=spec.version,
            adapter_id=spec.adapter_id,
            instrument_id=spec.instrument_id,
            compile_hash=compile_hash,
        )

    raise ValueError(f"unsupported compile profile: {profile}")
