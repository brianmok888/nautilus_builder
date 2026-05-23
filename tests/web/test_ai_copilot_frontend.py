from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ai_copilot_exposes_prompt_thread_audit_and_apply_surfaces() -> None:
    component = (ROOT / "apps" / "web" / "components" / "ai-builder" / "AiStrategyCopilot.tsx").read_text()
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "generateAiDraft" in api
    assert "applyAiDraftToBuilder" in api
    assert '"/api/ai-builder/apply"' in api
    assert "ai_thread_id" in component
    assert "improvement_cycle_id" in component
    assert "strategy_lineage_id" in component
    assert "strategy_version_id" in component
    assert "advisory" in component
    assert "Apply to Builder" in component
    assert "submit_order" not in component


def test_ai_copilot_apply_flow_requires_validated_draft_before_builder_update() -> None:
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "AI draft must pass validation before Apply to Builder" not in api
    assert "generateAiDraft(payload)" not in api
    assert "apiFetch<AiDraftApplication>" in api
