from services.api.app import create_app


def test_runtime_events_replay_route_is_mounted() -> None:
    response = create_app().get("/api/runtime-events/replay")

    payload = response.json()
    assert response.status_code == 200
    assert len(payload) == 2
    assert payload[0]["job_id"] == "bt_001"
    assert payload[0]["message"].startswith("Processed")


def test_strategy_registry_route_is_mounted() -> None:
    response = create_app().get("/api/strategy-registry/external")

    payload = response.json()
    assert response.status_code == 200
    assert payload
    assert {"strategy_id", "source", "classification", "read_only", "import_allowed"}.issubset(payload[0])


def test_ai_builder_draft_route_is_advisory_only() -> None:
    response = create_app().post(
        "/api/ai-builder/draft",
        json={"prompt": "Draft an EMA RSI pullback strategy"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["spec"]["stage"] == "draft"
    assert payload["accepted"] is True
    assert payload["spec"]["validation"]["output_mode"] == "signal_preview_only"


def test_ai_builder_apply_route_preserves_advisory_lineage_ids() -> None:
    response = create_app().post(
        "/api/ai-builder/apply",
        json={
            "prompt": "Draft an EMA RSI pullback strategy",
            "ai_thread_id": "ai_thread_001",
            "improvement_cycle_id": "cycle_001",
            "strategy_lineage_id": "lineage_strategy_001",
            "strategy_version_id": "strategy_001_v002",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ai_thread_id"] == "ai_thread_001"
    assert payload["improvement_cycle_id"] == "cycle_001"
    assert payload["strategy_lineage_id"] == "lineage_strategy_001"
    assert payload["strategy_version_id"] == "strategy_001_v002"
    assert payload["stage"] == "draft"
    assert payload["mode"] == "advisory_only"
    assert payload["spec"]["validation"]["output_mode"] == "signal_preview_only"


def test_shadow_promotion_route_is_contract_only() -> None:
    response = create_app().post(
        "/api/promotions/shadow",
        json={
            "strategy_version": "0.3.0-beta.1",
            "compile_hash": "abc123",
            "gate_compatibility": True,
            "evidence_refs": {
                "validation_report": "artifact://validation/vr_001.json",
                "backtest_result": "artifact://backtests/bt_001/result.json",
                "no_lookahead_report": "artifact://validation/no_lookahead_001.json",
                "gate_compatibility_report": "artifact://gate/gate_compat_001.json",
                "runtime_boundary_report": "artifact://runtime/boundary_001.json",
                "risk_review": "artifact://risk/risk_review_001.json",
            },
        },
    )

    payload = response.json()
    assert response.status_code == 201
    assert payload["profile"] == "signal_preview_only"
    assert payload["may_submit_order"] is False
    assert payload["may_create_trade_action"] is False


def test_promotion_request_route_exposes_shadow_only_manual_approval_contract() -> None:
    response = create_app().post(
        "/api/promotions/request",
        json={"strategy_version_id": "strategy_001_v002", "result_id": "res_001", "target": "shadow"},
    )

    payload = response.json()
    assert response.status_code == 201
    assert payload["strategy_version_id"] == "strategy_001_v002"
    assert payload["result_id"] == "res_001"
    assert payload["target"] == "shadow"
    assert payload["approval_state"] == "manual_approval_pending"
    assert payload["manual_approval_required"] is True
    assert payload["may_submit_order"] is False
    assert payload["may_create_trade_action"] is False


def test_promotion_request_route_rejects_live_targets() -> None:
    response = create_app().post(
        "/api/promotions/request",
        json={"strategy_version_id": "strategy_001_v002", "result_id": "res_001", "target": "live"},
    )

    assert response.status_code == 422
    assert response.json()["error"] == "unsupported_promotion_target"
