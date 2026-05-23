from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ai_copilot_exposes_prompt_thread_audit_and_apply_surfaces() -> None:
    component = (ROOT / "apps" / "web" / "components" / "ai-builder" / "AiStrategyCopilot.tsx").read_text()
    api = (ROOT / "apps" / "web" / "lib" / "api.ts").read_text()

    assert "generateAiDraft" in api
    assert "applyAiDraftToBuilder" in api
    assert "ai_thread_id" in component
    assert "improvement_cycle_id" in component
    assert "advisory" in component
    assert "Apply to Builder" in component
    assert "submit_order" not in component
