from __future__ import annotations

from typing import Protocol


class DraftProviderProtocol(Protocol):
    def draft_spec(self, prompt: str) -> dict[str, object]: ...


class AdvisoryDraftProvider:
    def draft_spec(self, prompt: str) -> dict[str, object]:
        return {
            "name": "EMA RSI Pullback Draft",
            "status": "draft",
            "stage": "draft",
            "output": "signal_preview_only",
            "indicators": [
                {"type": "EMA", "input": "close", "period": 20},
                {"type": "RSI", "input": "close", "period": 14},
            ],
            "entry": {"all": [{"crossed_above": ["close", "EMA_20"]}]},
            "exit": {"all": [{"gt": ["RSI_14", 70]}]},
            "risk": {"max_position_size": 1.0},
        }


class RecordedAiDraftStore:
    def __init__(self) -> None:
        self._records: list[dict[str, object]] = []

    def save(self, record: dict[str, object]) -> None:
        self._records.append(dict(record))

    def records_for_thread(self, ai_thread_id: str) -> list[dict[str, object]]:
        return [record for record in self._records if record["ai_thread_id"] == ai_thread_id]
