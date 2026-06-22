"""InstructorDraftProvider — typed LLM draft extraction behind DraftProviderProtocol.

Adoption Report §3.1. This is an EXTRACTION-ONLY provider:
  - It produces typed draft dicts via Pydantic validation (instructor).
  - It does NOT replace validate_strategy_spec, static safety scan, manual
    approval, or promotion evidence gates.
  - It has NO tools, NO agent invocation, NO order authority, NO runtime
    mutation, NO config mutation.

Authority flow (unchanged):
  operator prompt
    -> AiBuilderService._reject_forbidden_prompt  (credential/order rejection)
    -> InstructorDraftProvider.draft_spec          (typed draft extraction)
    -> validate_strategy_spec                      (Builder hard rules)
    -> audit record + manual promotion / evidence gates

The instructor client is INJECTABLE so tests run without an API key or network.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, ValidationError

# ---------------------------------------------------------------------------
# Draft model — mirrors the StrategySpec draft shape but locks advisory fields.
# Domain semantics (rule references, data-range validity, risk presence) are
# validated separately by validate_strategy_spec. This model only guarantees
# structural shape and advisory-stage invariants.
# ---------------------------------------------------------------------------


class StrategySpecDraftModel(BaseModel):
    """Pydantic model for instructor-typed LLM output.

    ``extra="forbid"`` ensures the model cannot smuggle in rogue fields like
    ``submit_order`` or credential strings. The ``Literal`` fields lock the
    output to the advisory draft lifecycle: it can never claim to be live,
    approved, active, or frozen by the model alone.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    version: str
    stage: Literal["draft"]
    status: Literal["draft"]
    created_from: Literal["ai_builder"]
    is_frozen: Literal[False]

    adapter_id: str
    venue: str
    instrument_id: str
    bar_type: str

    data_range: dict[str, object]
    indicators: dict[str, object]
    rules: dict[str, object]
    risk: dict[str, object]
    validation: dict[str, object]
    provenance: dict[str, object]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InstructorProviderConfig:
    """Configuration for the instructor provider.

    ``api_key_env`` is the NAME of the environment variable holding the key,
    never the key value itself — so it is safe to log metadata.
    """

    provider: str
    model: str
    api_key_env: str
    base_url: str | None = None
    timeout_secs: float = 30.0
    max_retries: int = 2

    def __post_init__(self) -> None:
        if self.timeout_secs <= 0:
            raise ValueError("timeout_secs must be positive")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least 1")


# ---------------------------------------------------------------------------
# Instructor client protocol (for type-hint + testability)
# ---------------------------------------------------------------------------


class _InstructorLike(Protocol):
    def create(
        self,
        *,
        response_model: type,
        messages: list[dict[str, str]],
        max_retries: int,
        **kwargs: Any,
    ) -> Any: ...


# ---------------------------------------------------------------------------
# System prompt — advisory-only constraints, no executable authority
# ---------------------------------------------------------------------------


def _strategy_spec_system_prompt() -> str:
    return (
        "Return JSON only: no markdown, no prose, no code blocks. "
        "Required top-level fields: schema_version, version, stage, status, created_from, is_frozen. "
        "Use stage='draft', status='draft', created_from='ai_builder', is_frozen=false. "
        "Include adapter_id, venue, instrument_id, bar_type, data_range, indicators, rules, risk, validation, provenance. "
        "Use validation.output_mode='signal_preview_only', validation.bar_close_only=true. "
        "validation.no_lookahead_required=true, validation.requires_backtest_before_shadow=true. "
        "Never include submit_order, TradeAction, credentials, api_key, secret_key, broker_order, exchange_order, "
        "shell code, imports, or live executable instructions."
    )


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

# Metadata allow-list: only these keys survive into last_metadata().
# This guarantees no secret/key/token leaks into audit metadata.
_METADATA_ALLOWLIST = frozenset({"provider", "model", "base_url_host", "response_model"})


class InstructorDraftProvider:
    """Extraction-only draft provider backed by an instructor client.

    The instructor client is injectable (``instructor_client``) so that tests
    run without network or credentials. At production-wiring time the client is
    built lazily from the OpenAI-compatible (or other) SDK via
    ``instructor.from_openai``.
    """

    def __init__(
        self,
        *,
        config: InstructorProviderConfig,
        instructor_client: _InstructorLike | None = None,
    ) -> None:
        self._config = config
        self._client: _InstructorLike | None = instructor_client
        self._last_metadata: dict[str, object] = {
            "provider": "instructor",
            "model": config.model,
            "response_model": "StrategySpecDraftModel",
        }

    def _ensure_client(self) -> _InstructorLike:
        if self._client is not None:
            return self._client
        self._client = self._build_client()
        return self._client

    def _build_client(self) -> _InstructorLike:
        """Build the instructor client lazily from the configured provider SDK.

        Kept minimal: the primary supported path is OpenAI-compatible.
        ``instructor`` and the provider SDK (e.g. ``openai``) are optional
        dependencies in the ``[ai]`` extra. Importing here avoids requiring
        them for the fixture/OpenAI-compatible/test paths.
        """
        try:
            import instructor  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - exercised in envs without [ai]
            raise ValueError(
                "instructor provider requires the [ai] extra: pip install -e '.[ai]'"
            ) from exc

        api_key = _read_api_key(self._config.api_key_env)
        host = _host_from_base_url(self._config.base_url)

        if self._config.provider in {"openai", "openai_compatible"}:
            try:
                from openai import OpenAI  # type: ignore[import-not-found]
            except ImportError as exc:  # pragma: no cover
                raise ValueError("openai SDK is required for the instructor openai provider") from exc
            raw = OpenAI(api_key=api_key, base_url=self._config.base_url, timeout=self._config.timeout_secs)
            client = instructor.from_openai(raw)
        elif self._config.provider == "ollama":
            try:
                from openai import OpenAI  # type: ignore[import-not-found]
            except ImportError as exc:  # pragma: no cover
                raise ValueError("openai SDK is required for the instructor ollama provider") from exc
            raw = OpenAI(api_key=api_key or "ollama", base_url=self._config.base_url or "http://localhost:11434/v1", timeout=self._config.timeout_secs)
            client = instructor.from_openai(raw)
        else:
            raise ValueError(f"unsupported instructor provider backend: {self._config.provider}")

        # Scrub the host into metadata (not the full URL, which could carry creds).
        self._last_metadata["base_url_host"] = host
        return cast(_InstructorLike, client)

    def draft_spec(self, prompt: str) -> dict[str, object]:
        """Extract a typed StrategySpec draft from the prompt.

        Returns a JSON-serializable dict. Raises ``ValueError`` on any failure
        (validation, network, provider) — callers (AiBuilderService) catch this
        and produce a rejected AiDraftResult. Never returns partial output.
        """
        client = self._ensure_client()
        messages = [
            {"role": "system", "content": _strategy_spec_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        # Provider-level retry loop (defense-in-depth alongside instructor's
        # internal retry). Catches validation failures and retries up to
        # max_retries before failing closed. Non-validation errors fail immediately.
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                draft = client.create(
                    response_model=StrategySpecDraftModel,
                    messages=messages,
                    max_retries=1,
                )
                break
            except ValidationError as exc:
                last_error = exc
                continue
            except Exception as exc:
                raise ValueError(f"instructor provider request failed: {exc}") from exc
        else:
            raise ValueError(f"instructor draft validation failed after {self._config.max_retries} retries: {last_error}") from last_error

        if not isinstance(draft, StrategySpecDraftModel):
            raise ValueError("instructor provider returned a non-StrategySpecDraftModel object")

        spec_dict = draft.model_dump(mode="json")
        # Defense-in-depth: guarantee advisory invariants survive serialization.
        _assert_advisory_invariants(spec_dict)
        return spec_dict

    def last_metadata(self) -> dict[str, object]:
        """Return scrubbed metadata. Only allow-listed keys survive."""
        scrubbed: dict[str, object] = {}
        for key in _METADATA_ALLOWLIST:
            if key in self._last_metadata:
                scrubbed[key] = self._last_metadata[key]
        return scrubbed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SECRET_VALUE_PATTERNS = ("sk-", "Bearer ", "api_key", "secret", "token", "password")


def _read_api_key(env_var: str) -> str:
    import os

    value = os.environ.get(env_var, "").strip()
    if not value:
        raise ValueError(f"instructor provider requires API key in env var {env_var}")
    return value


def _host_from_base_url(base_url: str | None) -> str:
    if not base_url:
        return "default"
    # Strip scheme and any userinfo@ before host.
    stripped = base_url
    for scheme in ("https://", "http://"):
        if stripped.startswith(scheme):
            stripped = stripped[len(scheme):]
    stripped = stripped.split("@")[-1]
    return stripped.split("/")[0]


def _assert_advisory_invariants(spec: dict[str, object]) -> None:
    """Final guard: the dict must remain advisory-only after serialization."""
    if spec.get("stage") != "draft":
        raise ValueError("instructor draft has non-draft stage")
    if spec.get("status") != "draft":
        raise ValueError("instructor draft has non-draft status")
    if spec.get("created_from") != "ai_builder":
        raise ValueError("instructor draft has non-ai_builder created_from")
    if spec.get("is_frozen") is not False:
        raise ValueError("instructor draft is frozen")
    # Scan for forbidden authority/credential terms in string values.
    blob = str(spec).lower()
    for forbidden in ("submit_order", "tradeaction", "place_order", "live_order"):
        if forbidden in blob:
            raise ValueError(f"instructor draft contains forbidden authority term: {forbidden}")
