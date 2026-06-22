from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import ssl
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from sqlite3 import Connection
from typing import Protocol


def _default_httpx_transport() -> OpenAITransport:
    """Build a default HttpxJsonTransport wrapped to match the OpenAITransport signature.

    Replaces the raw ``_urllib_json_transport`` default with httpx for explicit
    timeouts and TLS verification (Adoption Report §4.1 / P2-5).
    """
    from packages.ai_builder.http_transport import HttpxJsonTransport

    def _transport(url: str, headers: dict[str, str], payload: dict[str, object], timeout_secs: float) -> dict[str, object]:
        # Use a fresh transport honoring the per-call timeout (not the 30s default).
        per_call = HttpxJsonTransport(timeout_secs=timeout_secs, verify=True)
        return per_call.post_json(url=url, headers=headers, payload=payload)

    return _transport


class DraftProviderProtocol(Protocol):
    def draft_spec(self, prompt: str) -> dict[str, object]: ...


class DraftAuditStoreProtocol(Protocol):
    def save(self, record: dict[str, object]) -> None: ...


class AdvisoryDraftProvider:
    def draft_spec(self, prompt: str) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "version": "0.1.0-draft.1",
            "stage": "draft",
            "status": "draft",
            "created_from": "ai_builder",
            "is_frozen": False,
            "adapter_id": "BINANCE_PERP",
            "venue": "BINANCE",
            "instrument_id": "BTCUSDT-PERP",
            "bar_type": "BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
            "data_range": {
                "start": "2025-01-01T00:00:00Z",
                "end": "2025-06-01T00:00:00Z",
            },
            "indicators": {
                "ema_fast": {"type": "EMA", "input": "close", "period": 20},
                "ema_slow": {"type": "EMA", "input": "close", "period": 50},
                "rsi": {"type": "RSI", "input": "close", "period": 14},
            },
            "rules": {
                "long_entry": {
                    "all": [
                        {"crossed_above": ["ema_fast", "ema_slow"]},
                        {"gt": ["rsi", 52]},
                    ]
                },
                "long_exit": {
                    "any": [
                        {"crossed_below": ["ema_fast", "ema_slow"]},
                        {"lt": ["rsi", 45]},
                    ]
                },
            },
            "risk": {
                "position_size_pct": 0.05,
                "stop_loss_pct": 0.012,
                "take_profit_pct": 0.024,
                "max_hold_bars": 48,
            },
            "validation": {
                "bar_close_only": True,
                "no_lookahead_required": True,
                "requires_backtest_before_shadow": True,
                "output_mode": "signal_preview_only",
            },
            "provenance": {
                "created_by": "ai_builder",
                "parent_version_id": None,
            },
        }

    def last_metadata(self) -> dict[str, object]:
        return {"provider": "advisory_fixture"}


OpenAITransport = Callable[
    [str, dict[str, str], dict[str, object], float],
    dict[str, object],
]


@dataclass(frozen=True)
class OpenAICompatibleProviderConfig:
    api_key: str = field(repr=False)
    base_url: str
    model: str
    timeout_secs: float = 30.0

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("OPENAI_API_KEY is required")
        if not self.base_url.strip():
            raise ValueError("OPENAI_BASE_URL is required")
        if not self.model.strip():
            raise ValueError("OPENAI_MODEL is required")
        if self.timeout_secs <= 0:
            raise ValueError("timeout_secs must be positive")

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "OpenAICompatibleProviderConfig | None":
        env = os.environ if environ is None else environ
        api_key = env.get("OPENAI_API_KEY", "").strip()
        base_url = env.get("OPENAI_BASE_URL", "").strip()
        model = env.get("OPENAI_MODEL", "").strip()
        if not (api_key and base_url and model):
            return None
        timeout_raw = env.get("OPENAI_TIMEOUT_SECS", "30").strip() or "30"
        try:
            timeout_secs = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("OPENAI_TIMEOUT_SECS must be numeric") from exc
        return cls(api_key=api_key, base_url=base_url, model=model, timeout_secs=timeout_secs)

    @property
    def chat_completions_url(self) -> str:
        return _chat_completions_url(self.base_url)


class OpenAICompatibleDraftProvider:
    def __init__(
        self,
        config: OpenAICompatibleProviderConfig,
        *,
        transport: OpenAITransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or _default_httpx_transport()
        self._last_metadata: dict[str, object] = {
            "provider": "openai_compatible",
            "model": config.model,
            "endpoint_url": config.chat_completions_url,
        }

    def draft_spec(self, prompt: str) -> dict[str, object]:
        endpoint_url = self._config.chat_completions_url
        payload = _build_chat_completions_payload(self._config.model, prompt)
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = self._transport(endpoint_url, headers, payload, self._config.timeout_secs)
        self._last_metadata = _response_metadata(
            response,
            model=self._config.model,
            endpoint_url=endpoint_url,
        )
        content = _extract_message_content(response)
        spec = _parse_strategy_spec_content(content)
        return spec

    def last_metadata(self) -> dict[str, object]:
        return dict(self._last_metadata)


class RecordedAiDraftStore:
    def __init__(self) -> None:
        self._records: list[dict[str, object]] = []

    def save(self, record: dict[str, object]) -> None:
        self._records.append(dict(record))

    def records_for_thread(self, ai_thread_id: str) -> list[dict[str, object]]:
        return [record for record in self._records if record["ai_thread_id"] == ai_thread_id]


class SqliteAiDraftAuditStore:
    def __init__(self, *, connection: Connection) -> None:
        self._connection = connection
        self._connection.execute(
            """
            create table if not exists builder_ai_draft_audit (
                sequence integer primary key autoincrement,
                ai_thread_id text not null,
                payload text not null
            )
            """
        )
        self._connection.commit()

    def save(self, record: dict[str, object]) -> None:
        self._connection.execute(
            "insert into builder_ai_draft_audit (ai_thread_id, payload) values (?, ?)",
            (str(record["ai_thread_id"]), json.dumps(record, sort_keys=True, separators=(",", ":"))),
        )
        self._connection.commit()

    def records_for_thread(self, ai_thread_id: str) -> list[dict[str, object]]:
        rows = self._connection.execute(
            "select payload from builder_ai_draft_audit where ai_thread_id = ? order by sequence",
            (ai_thread_id,),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]


def build_default_draft_provider(environ: Mapping[str, str] | None = None) -> DraftProviderProtocol:
    env = environ if environ is not None else __import__("os").environ
    provider_kind = env.get("BUILDER_AI_PROVIDER", "").strip().lower()
    if provider_kind == "instructor":
        from packages.ai_builder.instructor_provider import (
            InstructorDraftProvider,
            InstructorProviderConfig,
        )
        inst_config = InstructorProviderConfig(
            provider=env.get("BUILDER_INSTRUCTOR_PROVIDER", "openai").strip().lower(),
            model=env.get("BUILDER_INSTRUCTOR_MODEL", "").strip(),
            api_key_env=env.get("BUILDER_INSTRUCTOR_API_KEY_ENV", "BUILDER_AI_API_KEY").strip(),
            base_url=env.get("BUILDER_INSTRUCTOR_BASE_URL") or None,
            timeout_secs=float(env.get("BUILDER_INSTRUCTOR_TIMEOUT_SECS", "30")),
            max_retries=int(env.get("BUILDER_INSTRUCTOR_MAX_RETRIES", "2")),
        )
        return InstructorDraftProvider(config=inst_config)
    config = OpenAICompatibleProviderConfig.from_env(environ)
    if config is not None:
        return OpenAICompatibleDraftProvider(config)
    return AdvisoryDraftProvider()


def _build_chat_completions_payload(model: str, prompt: str) -> dict[str, object]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": _strategy_spec_system_prompt(),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }


def _strategy_spec_system_prompt() -> str:
    return (
        "You convert operator strategy descriptions into one strict Nautilus Builder StrategySpec JSON object. "
        "Return JSON only: no Markdown, no prose, no code fences. "
        "Required top-level fields: schema_version, version, stage, status, created_from, is_frozen, "
        "adapter_id, venue, instrument_id, bar_type, data_range, indicators, rules, risk, validation, provenance. "
        "Use stage='draft', status='draft', created_from='ai_builder', provenance.created_by='ai_builder'. "
        "Use validation.output_mode='signal_preview_only', validation.bar_close_only=true, "
        "validation.no_lookahead_required=true, validation.requires_backtest_before_shadow=true. "
        "Never include submit_order, TradeAction, credentials, api_key, secret_key, broker_order, exchange_order, "
        "live execution instructions, shell code, imports, or executable code. "
        "The draft is advisory-only and must require validation and backtest before manual promotion."
    )


def _chat_completions_url(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _urllib_json_transport(
    url: str,
    headers: dict[str, str],
    payload: dict[str, object],
    timeout_secs: float,
) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        # The endpoint is explicit operator configuration; never derived from model output.
        # Explicit TLS context: certificate verification is required and hostname
        # checking is on. Never derived from model output.
        _ssl_context = ssl.create_default_context()
        with urllib.request.urlopen(request, timeout=timeout_secs, context=_ssl_context) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace").strip()
        suffix = f": {details[:300]}" if details else ""
        raise ValueError(f"OpenAI-compatible provider HTTP {exc.code}{suffix}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"OpenAI-compatible provider request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise ValueError("OpenAI-compatible provider request timed out") from exc

    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenAI-compatible provider returned non-JSON response metadata") from exc
    if not isinstance(decoded, dict):
        raise ValueError("OpenAI-compatible provider returned non-object response metadata")
    return decoded


def _extract_message_content(response: dict[str, object]) -> object:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenAI-compatible provider response missing choices")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ValueError("OpenAI-compatible provider response choice is not an object")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise ValueError("OpenAI-compatible provider response missing message")
    if "content" not in message:
        raise ValueError("OpenAI-compatible provider response missing message content")
    return message["content"]


def _parse_strategy_spec_content(content: object) -> dict[str, object]:
    if isinstance(content, dict):
        return dict(content)
    if not isinstance(content, str):
        raise ValueError("OpenAI-compatible provider must return strict StrategySpec JSON content")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("OpenAI-compatible provider must return strict StrategySpec JSON content") from exc
    if not isinstance(parsed, dict):
        raise ValueError("OpenAI-compatible provider StrategySpec content must be a JSON object")
    return parsed


def _response_metadata(response: dict[str, object], *, model: str, endpoint_url: str) -> dict[str, object]:
    choices = response.get("choices")
    first_choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
    metadata: dict[str, object] = {
        "provider": "openai_compatible",
        "model": model,
        "endpoint_url": endpoint_url,
    }
    response_id = response.get("id")
    if isinstance(response_id, str):
        metadata["response_id"] = response_id
    response_model = response.get("model")
    if isinstance(response_model, str):
        metadata["response_model"] = response_model
    finish_reason = first_choice.get("finish_reason") if isinstance(first_choice, dict) else None
    if isinstance(finish_reason, str):
        metadata["finish_reason"] = finish_reason
    usage = response.get("usage")
    if isinstance(usage, dict):
        metadata["usage"] = dict(usage)
    return metadata
