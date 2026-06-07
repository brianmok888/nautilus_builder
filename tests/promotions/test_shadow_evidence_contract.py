from __future__ import annotations  # noqa: E402

import pytest  # noqa: E402

from packages.promotions.service import PromotionService  # noqa: E402
from services.api.app import create_app  # noqa: E402


REQUIRED_EVIDENCE = {
    "validation_report": "artifact://validation/vr_001.json",
    "backtest_result": "artifact://backtests/bt_001/result.json",
    "no_lookahead_report": "artifact://validation/no_lookahead_001.json",
    "gate_compatibility_report": "artifact://gate/gate_compat_001.json",
    "runtime_boundary_report": "artifact://runtime/boundary_001.json",
    "risk_review": "artifact://risk/risk_review_001.json",
}


def test_shadow_request_rejects_missing_required_evidence_refs() -> None:
    with pytest.raises(ValueError, match="promotion evidence missing"):
        PromotionService().create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs={"validation_report": "artifact://validation/vr_001.json"},
        )


def test_shadow_request_rejects_failed_gate_compatibility() -> None:
    with pytest.raises(ValueError, match="gate compatibility evidence is required"):
        PromotionService().create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=False,
            evidence_refs=REQUIRED_EVIDENCE,
        )


def test_shadow_request_carries_explicit_evidence_refs_without_fabrication() -> None:
    request = PromotionService(allow_legacy_fixture_refs=True).create_shadow_request(
        strategy_version="0.3.0-beta.1",
        compile_hash="abc123",
        gate_compatibility=True,
        evidence_refs=REQUIRED_EVIDENCE,
    )

    assert request.evidence_refs == REQUIRED_EVIDENCE
    assert request.gate_compatibility is True
    assert request.may_submit_order is False
    assert request.may_create_trade_action is False


def test_shadow_route_rejects_missing_evidence_payload() -> None:
    response = create_app().post(
        "/api/promotions/shadow",
        json={"strategy_version": "0.3.0-beta.1", "compile_hash": "abc123"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "promotion_evidence_missing"


def test_shadow_route_accepts_explicit_evidence_payload() -> None:
    response = create_shadow_payload(
        {
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": True,
            "evidence_refs": REQUIRED_EVIDENCE,
        },
        strict_evidence=False,
    )

    payload = response.json()
    assert response.status_code == 201
    assert payload["evidence_refs"] == REQUIRED_EVIDENCE
    assert payload["profile"] == "signal_preview_only"
    assert payload["may_submit_order"] is False


def test_shadow_route_rejects_string_gate_compatibility_even_with_complete_evidence() -> None:
    response = create_app().post(
        "/api/promotions/shadow",
        json={
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": "false",
            "evidence_refs": REQUIRED_EVIDENCE,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "promotion_evidence_missing"


def test_shadow_route_rejects_non_string_evidence_refs() -> None:
    evidence_refs = dict(REQUIRED_EVIDENCE)
    evidence_refs["risk_review"] = 123

    response = create_app().post(
        "/api/promotions/shadow",
        json={
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": True,
            "evidence_refs": evidence_refs,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "promotion_evidence_missing"


def test_shadow_route_rejects_empty_evidence_refs() -> None:
    evidence_refs = dict(REQUIRED_EVIDENCE)
    evidence_refs["risk_review"] = ""

    response = create_app().post(
        "/api/promotions/shadow",
        json={
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": True,
            "evidence_refs": evidence_refs,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "promotion_evidence_missing"


def test_shadow_route_rejects_missing_strategy_version_or_compile_hash() -> None:
    response = create_app().post(
        "/api/promotions/shadow",
        json={
            "strategy_version": "0.3.0-beta.1",
            "gate_compatibility": True,
            "evidence_refs": REQUIRED_EVIDENCE,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "promotion_evidence_missing"

from packages.artifact_store import LocalJsonArtifactStore  # noqa: E402
from packages.auth import ProjectScopeError, UserProjectContext  # noqa: E402
from services.api.routes.promotions import create_shadow_payload  # noqa: E402

import warnings  # noqa: E402

warnings.filterwarnings("ignore", message="allow_legacy_fixture_refs=True is deprecated", category=DeprecationWarning)


STRICT_EVIDENCE_KEYS = (
    "validation_report",
    "backtest_result",
    "no_lookahead_report",
    "gate_compatibility_report",
    "runtime_boundary_report",
    "risk_review",
)


def _strict_artifact_refs(tmp_path, context: UserProjectContext) -> tuple[LocalJsonArtifactStore, dict[str, str]]:
    store = LocalJsonArtifactStore(root=tmp_path / "artifacts")
    refs: dict[str, str] = {}
    for key in STRICT_EVIDENCE_KEYS:
        record = store.put_json(
            context=context,
            artifact_type=key,
            artifact_id=f"{key}_001",
            payload={"evidence_type": key, "compile_hash": "abc123", "strategy_version": "0.3.0-beta.1", "orders": 0},
            metadata={"evidence_type": key, "compile_hash": "abc123", "strategy_version": "0.3.0-beta.1"},
        )
        refs[key] = record.artifact_ref
    return store, refs


def test_strict_shadow_request_resolves_scoped_artifacts_and_records_checksums(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, refs = _strict_artifact_refs(tmp_path, context)

    request = PromotionService(artifact_store=store, context=context).create_shadow_request(
        strategy_version="0.3.0-beta.1",
        compile_hash="abc123",
        gate_compatibility=True,
        evidence_refs=refs,
    )

    assert request.evidence_refs == refs
    assert set(request.evidence_checksums) == set(STRICT_EVIDENCE_KEYS)
    assert all(len(checksum) == 64 for checksum in request.evidence_checksums.values())
    assert request.may_submit_order is False


def test_strict_shadow_request_rejects_legacy_unscoped_refs(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, _refs = _strict_artifact_refs(tmp_path, context)

    with pytest.raises(ValueError, match="scoped Builder artifact refs required"):
        PromotionService(artifact_store=store, context=context).create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs=REQUIRED_EVIDENCE,
        )


def test_strict_shadow_request_rejects_wrong_artifact_type(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, refs = _strict_artifact_refs(tmp_path, context)
    wrong = store.put_json(
        context=context,
        artifact_type="wrong_risk_review",
        artifact_id="risk_review_001",
        payload={"evidence_type": "wrong_risk_review"},
    )
    refs["risk_review"] = wrong.artifact_ref

    with pytest.raises(ValueError, match="artifact type mismatch: risk_review expected risk_review, got wrong_risk_review"):
        PromotionService(artifact_store=store, context=context).create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs=refs,
        )


def test_strict_shadow_request_rejects_checksum_mismatch(tmp_path) -> None:
    import json  # noqa: E402

    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, refs = _strict_artifact_refs(tmp_path, context)
    risk_path = tmp_path / "artifacts" / "project_alpha" / "user_123" / "risk_review" / "risk_review_001.json"
    envelope = json.loads(risk_path.read_text())
    envelope["payload"]["orders"] = 99
    risk_path.write_text(json.dumps(envelope))

    with pytest.raises(ValueError, match="artifact checksum mismatch"):
        PromotionService(artifact_store=store, context=context).create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs=refs,
        )


def test_strict_shadow_request_rejects_cross_project_evidence(tmp_path) -> None:
    owner = UserProjectContext(user_id="user_123", project_id="project_alpha")
    intruder = UserProjectContext(user_id="user_123", project_id="project_beta")
    store, refs = _strict_artifact_refs(tmp_path, owner)

    with pytest.raises(ProjectScopeError, match="outside user/project scope"):
        PromotionService(artifact_store=store, context=intruder).create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs=refs,
        )


def test_strict_shadow_route_resolves_artifact_evidence(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, refs = _strict_artifact_refs(tmp_path, context)

    response = create_shadow_payload(
        {
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": True,
            "evidence_refs": refs,
        },
        context=context,
        artifact_store=store,
        strict_evidence=True,
    )

    assert response.status_code == 201
    assert response.json()["evidence_refs"] == refs
    assert set(response.json()["evidence_checksums"]) == set(STRICT_EVIDENCE_KEYS)


def test_strict_shadow_route_rejects_legacy_refs(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, _refs = _strict_artifact_refs(tmp_path, context)

    response = create_shadow_payload(
        {
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": True,
            "evidence_refs": REQUIRED_EVIDENCE,
        },
        context=context,
        artifact_store=store,
        strict_evidence=True,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "promotion_evidence_missing"
    assert "scoped Builder artifact refs required" in response.json()["details"]


def test_strict_shadow_request_rejects_missing_scoped_artifact_as_domain_error(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, refs = _strict_artifact_refs(tmp_path, context)
    refs["risk_review"] = "artifact://builder/project_alpha/user_123/risk_review/missing_risk_review"

    with pytest.raises(ValueError, match="artifact not found"):
        PromotionService(artifact_store=store, context=context).create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs=refs,
        )


def test_strict_shadow_request_rejects_wrong_compile_hash_evidence(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, refs = _strict_artifact_refs(tmp_path, context)
    stale = store.put_json(
        context=context,
        artifact_type="backtest_result",
        artifact_id="stale_compile",
        payload={
            "evidence_type": "backtest_result",
            "compile_hash": "old_compile_hash",
            "strategy_version": "0.3.0-beta.1",
        },
        metadata={"compile_hash": "old_compile_hash", "strategy_version": "0.3.0-beta.1"},
    )
    refs["backtest_result"] = stale.artifact_ref

    with pytest.raises(ValueError, match="compile_hash mismatch"):
        PromotionService(artifact_store=store, context=context).create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs=refs,
        )


def test_strict_shadow_request_rejects_wrong_strategy_version_evidence(tmp_path) -> None:
    context = UserProjectContext(user_id="user_123", project_id="project_alpha")
    store, refs = _strict_artifact_refs(tmp_path, context)
    stale = store.put_json(
        context=context,
        artifact_type="validation_report",
        artifact_id="stale_strategy_version",
        payload={
            "evidence_type": "validation_report",
            "compile_hash": "abc123",
            "strategy_version": "0.2.0-beta.9",
        },
        metadata={"compile_hash": "abc123", "strategy_version": "0.2.0-beta.9"},
    )
    refs["validation_report"] = stale.artifact_ref

    with pytest.raises(ValueError, match="strategy_version mismatch"):
        PromotionService(artifact_store=store, context=context).create_shadow_request(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            evidence_refs=refs,
        )
