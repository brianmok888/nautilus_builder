from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "apps" / "web"


def test_config_route_mounts_advisory_llm_config_tabs() -> None:
    page = (WEB / "app" / "config" / "page.tsx").read_text()
    component = (WEB / "components" / "config" / "ModelConfigTabs.tsx").read_text()
    shell = (WEB / "components" / "shell" / "OperatorAppShell.tsx").read_text()

    assert "ModelConfigTabs" in page
    assert "href=\"/config\"" in shell
    assert "Tabs" in component
    assert "OPENAI_BASE_URL" in component
    assert "OPENAI_MODEL" in component
    assert "OPENAI_API_KEY stays server-side only" in component
    assert "validate_strategy_spec() is mandatory" in component
    assert "submit_order / TradeAction blocked" in component
    assert 'type="password"' not in component
    assert 'name="apiKey"' not in component
    assert "secret_key" not in component.lower()
