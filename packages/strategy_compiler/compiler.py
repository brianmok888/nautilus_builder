"""Strategy compiler — compiles StrategySpec payloads into CompileArtifacts.

Supports both classic_v1 and microstructure_v1 schema families.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from packages.strategy_spec.microstructure import StrategySpecMicrostructureV1
from packages.strategy_spec.models import StrategySpec
from packages.strategy_spec.resolver import get_spec_family_name, parse_strategy_spec

from .artifacts import CompileArtifact


def _stable_payload_hash(payload: dict[str, Any], profile: str) -> str:
    encoded = json.dumps({"profile": profile, "payload": payload}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def compile_strategy_spec(payload: dict[str, Any], *, profile: str) -> CompileArtifact:
    """Compile a strategy spec payload into a CompileArtifact.

    Handles both classic_v1 and microstructure_v1 schema families.
    Classic specs support backtest and signal_preview_only profiles.
    Microstructure specs compile only to signal_preview_only.
    """
    family = get_spec_family_name(payload)
    spec = parse_strategy_spec(payload)
    compile_hash = _stable_payload_hash(spec.model_dump(mode="json"), profile)

    if family == "microstructure_v1":
        # Microstructure specs compile only to signal_preview_only
        return CompileArtifact(
            profile="signal_preview_only",
            strategy_class="RuleGraphMicrostructureStrategy",
            output_mode="signal_preview_only",
            execution_authority=False,
            spec_version=spec.version,
            adapter_id=spec.adapter_id,
            instrument_id=spec.instrument_id,
            compile_hash=compile_hash,
        )

    # Classic specs
    assert isinstance(spec, StrategySpec)
    if profile == "backtest":
        return CompileArtifact(
            profile="backtest",
            strategy_class="RuleGraphBacktestStrategy",
            output_mode="backtest_signal_observation",
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


def compile_strategy_spec_bundle(
    payload: dict[str, Any], *, profile: str
) -> dict[str, Any]:
    """Compile a strategy spec into a full deterministic artifact bundle.

    Produces:
    - compiled_strategy_ir.json
    - feature_dependency_graph.json
    - risk_contract.json
    - replay_manifest_template.json
    - compile_report.json
    - artifact_bundle_manifest.json

    Returns a dict with all artifacts keyed by name.
    """
    from packages.strategy_compiler.hashing import canonical_hash
    from packages.strategy_compiler.ir import CompiledStrategyIR
    from packages.strategy_spec.resolver import get_spec_family_name, parse_strategy_spec

    family = get_spec_family_name(payload)
    spec = parse_strategy_spec(payload)
    spec_dump = spec.model_dump(mode="json")
    spec_hash = canonical_hash(spec_dump)
    compile_hash = _stable_payload_hash(spec_dump, profile)

    # Build feature dependency graph
    feature_graph_data: dict[str, Any] = {
        "schema_version": "feature_dependency_graph_v1",
        "required_features": [],
        "optional_features": [],
        "source_health_requirements": [],
        "fail_closed_features": [],
    }
    if family == "microstructure_v1":
        for feat in spec.features:  # type: ignore[union-attr]
            feat_entry = {"feature": feat.feature.value, "required": feat.required}
            if feat.max_staleness_ms:
                feat_entry["max_staleness_ms"] = feat.max_staleness_ms
            if feat.required:
                feature_graph_data["required_features"].append(feat_entry)
                if feat.fail_closed_on_missing:
                    feature_graph_data["fail_closed_features"].append(feat_entry)
            else:
                feature_graph_data["optional_features"].append(feat_entry)
    else:
        # Classic: indicators as features
        for name, indicator in spec_dump.get("indicators", {}).items():
            feature_graph_data["required_features"].append(
                {"feature": f"{name}_{indicator['type']}", "required": True}
            )
    feature_graph_hash = canonical_hash(feature_graph_data)

    # Build risk contract
    risk_data: dict[str, Any] = {
        "schema_version": "risk_contract_v1",
        "max_position_notional_usd": None,
        "max_loss_notional_usd": None,
        "max_hold_ms": None,
        "max_spread_bps": None,
        "max_slippage_bps": None,
        "execution_authority": False,
    }
    if family == "microstructure_v1":
        risk = spec.risk  # type: ignore[union-attr]
        risk_data["max_position_notional_usd"] = risk.max_position_notional_usd
        risk_data["max_loss_notional_usd"] = risk.max_loss_notional_usd
        risk_data["max_hold_ms"] = risk.max_hold_ms
    else:
        risk_raw = spec_dump.get("risk", {})
        risk_data["max_position_notional_usd"] = risk_raw.get("position_size_pct")
    risk_contract_hash = canonical_hash(risk_data)

    # Build IR
    ir = CompiledStrategyIR(
        normalized_spec=spec_dump,
        compile_hash=compile_hash,
        feature_graph_hash=feature_graph_hash,
        risk_contract_hash=risk_contract_hash,
        condition_count=len(spec_dump.get("rules", {})) if family == "classic_v1" else len(spec.signals) if hasattr(spec, "signals") else 0,  # type: ignore[union-attr]
        feature_count=len(feature_graph_data["required_features"]) + len(feature_graph_data["optional_features"]),
        execution_authority=False,
    )
    ir_hash = canonical_hash(ir.model_dump(mode="json"))

    # Replay manifest template
    replay_manifest: dict[str, Any] = {
        "schema_version": "replay_manifest_template_v1",
        "strategy_spec_hash": spec_hash,
        "compile_hash": compile_hash,
        "required_datasets": ["quote_ticks"],
        "optional_datasets": ["trade_ticks", "bars_ohlcv"],
        "adapter_id": spec_dump.get("adapter_id", ""),
        "instrument_id": spec_dump.get("instrument_id", ""),
    }
    replay_manifest_hash = canonical_hash(replay_manifest)

    # Compile report
    from packages.builder_metadata.version import get_canonical_version
    compile_report: dict[str, Any] = {
        "schema_version": "compile_report_v1",
        "spec_family": family,
        "compile_hash": compile_hash,
        "spec_hash": spec_hash,
        "feature_graph_hash": feature_graph_hash,
        "risk_contract_hash": risk_contract_hash,
        "ir_hash": ir_hash,
        "compiler_version": get_canonical_version(),
        "profile": profile if family == "classic_v1" else "signal_preview_only",
        "execution_authority": False,
    }
    compile_report_hash = canonical_hash(compile_report)

    # Bundle manifest
    bundle_manifest: dict[str, Any] = {
        "schema_version": "artifact_bundle_manifest_v1",
        "strategy_spec_family": family,
        "strategy_spec_hash": spec_hash,
        "normalized_spec": spec_dump,
        "feature_graph_hash": feature_graph_hash,
        "risk_contract_hash": risk_contract_hash,
        "compiler_version": get_canonical_version(),
        "compiler_policy_hash": "",
        "execution_authority": False,
        "artifacts": {
            "compiled_strategy_ir": {"hash": ir_hash},
            "feature_dependency_graph": {"hash": feature_graph_hash},
            "risk_contract": {"hash": risk_contract_hash},
            "replay_manifest_template": {"hash": replay_manifest_hash},
            "compile_report": {"hash": compile_report_hash},
        },
    }
    bundle_manifest_hash = canonical_hash(bundle_manifest)
    bundle_manifest["artifact_bundle_hash"] = bundle_manifest_hash

    return {
        "compiled_strategy_ir": ir.model_dump(mode="json"),
        "feature_dependency_graph": feature_graph_data,
        "risk_contract": risk_data,
        "replay_manifest_template": replay_manifest,
        "compile_report": compile_report,
        "artifact_bundle_manifest": bundle_manifest,
    }
