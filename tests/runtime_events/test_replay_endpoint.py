from __future__ import annotations

from services.api.routes.runtime_events import replay_runtime_events_payload


def test_replay_endpoint_returns_persisted_events() -> None:
    payload = replay_runtime_events_payload()

    assert payload[0]["message"] == "Processed 2025-03-01 to 2025-03-15"
    assert payload[1]["progress_pct"] == 74.2
