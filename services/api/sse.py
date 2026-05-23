from __future__ import annotations

import json

from packages.runtime_events.models import RuntimeEvent


def format_runtime_event_sse(event: RuntimeEvent) -> str:
    payload = json.dumps(event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return f"event: runtime_event\ndata: {payload}\n\n"
