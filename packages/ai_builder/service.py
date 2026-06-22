from __future__ import annotations

import hashlib
from collections.abc import Mapping

from packages.strategy_validation.validators import validate_strategy_spec

from .models import AiDraftResult
from .provider import (
    AdvisoryDraftProvider,
    DraftAuditStoreProtocol,
    DraftProviderProtocol,
    RecordedAiDraftStore,
    build_default_draft_provider,
)


class AiBuilderService:
    def __init__(
        self,
        *,
        provider: DraftProviderProtocol | None = None,
        store: DraftAuditStoreProtocol | None = None,
    ) -> None:
        self._provider = provider or AdvisoryDraftProvider()
        self._store = store or RecordedAiDraftStore()

    @classmethod
    def from_env(
        cls,
        *,
        store: DraftAuditStoreProtocol | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> "AiBuilderService":
        return cls(provider=build_default_draft_provider(environ), store=store)

    def generate_draft(
        self,
        prompt: str,
        *,
        force_invalid: bool = False,
        include_forbidden_execution: bool = False,
        ai_thread_id: str = "anonymous_thread",
    ) -> AiDraftResult:
        _reject_forbidden_prompt(prompt, include_forbidden_execution=include_forbidden_execution)

        provider_error: str | None = None
        try:
            spec = self._provider.draft_spec(prompt)
        except ValueError as exc:
            spec = {}
            provider_error = str(exc)
        if force_invalid:
            spec.pop("risk", None)

        if provider_error is None:
            validation_report = validate_strategy_spec(spec)
            validation_errors = validation_report.errors
        else:
            validation_errors = [provider_error]

        if not validation_errors:
            result = AiDraftResult(
                spec=spec,
                accepted=True,
                validation_errors=[],
                explanation="Draft generated in advisory mode and kept in Draft lifecycle stage.",
            )
        else:
            result = AiDraftResult(
                spec=spec,
                accepted=False,
                validation_errors=validation_errors,
                explanation="Draft rejected until Builder schema and hard-rule validation pass.",
            )
        provider_metadata = _provider_metadata(self._provider)
        self._store.save(
            {
                "ai_thread_id": ai_thread_id,
                "mode": "advisory_only",
                "stage": "draft",
                "accepted": result.accepted,
                "prompt": _redact_prompt(prompt)[0],
                "prompt_hash": _redact_prompt(prompt)[1],
                "provider": provider_metadata.get("provider", type(self._provider).__name__),
                "provider_metadata": provider_metadata,
                "validation_errors": result.validation_errors,
                "spec": result.spec,
            }
        )
        return result

    def apply_draft_to_strategy(
        self,
        prompt: str,
        *,
        ai_thread_id: str,
        improvement_cycle_id: str,
        strategy_lineage_id: str,
        strategy_version_id: str,
        spec: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        _require_non_empty("ai_thread_id", ai_thread_id)
        _require_non_empty("improvement_cycle_id", improvement_cycle_id)
        _require_non_empty("strategy_lineage_id", strategy_lineage_id)
        _require_non_empty("strategy_version_id", strategy_version_id)
        if spec is None:
            result = self.generate_draft(prompt, ai_thread_id=ai_thread_id)
            if not result.accepted:
                raise ValueError("AI draft must pass validation before apply")
            applied_spec = result.spec
        else:
            applied_spec = dict(spec)
            validation_report = validate_strategy_spec(applied_spec)
            if validation_report.errors:
                raise ValueError("AI draft must pass validation before apply")
        record = {
            "ai_thread_id": ai_thread_id,
            "improvement_cycle_id": improvement_cycle_id,
            "strategy_lineage_id": strategy_lineage_id,
            "strategy_version_id": strategy_version_id,
            "stage": "draft",
            "mode": "advisory_only",
            "spec": applied_spec,
        }
        self._store.save(record)
        return record


def _require_non_empty(field_name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _provider_metadata(provider: DraftProviderProtocol) -> dict[str, object]:
    metadata_reader = getattr(provider, "last_metadata", None)
    if not callable(metadata_reader):
        return {"provider": type(provider).__name__}
    metadata = metadata_reader()
    if not isinstance(metadata, dict):
        return {"provider": type(provider).__name__}
    return dict(metadata)


def _redact_prompt(prompt: str) -> tuple[str, str]:
    """Redact secrets from prompt before audit storage. Returns (redacted_prompt, prompt_hash)."""
    import re
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    redacted = prompt
    secret_patterns = [
        r"(api[_-]?key[\'s]*[:=]\s*)[\w\-]{8,}",
        r"(secret[_-]?key[\'s]*[:=]\s*)[\w\-]{8,}",
        r"(token[\'s]*[:=]\s*)[\w\-]{8,}",
        r"(password[\'s]*[:=]\s*)\S+",
        r"(Bearer\s+)[\w\-\.]+",
    ]
    for pattern in secret_patterns:
        redacted = re.sub(pattern, r"\1[REDACTED]", redacted, flags=re.IGNORECASE)
    return redacted, prompt_hash



def _reject_forbidden_prompt(prompt: str, *, include_forbidden_execution: bool) -> None:
    lowered = prompt.lower()
    if include_forbidden_execution or "submit order" in lowered or "submit orders" in lowered:
        raise ValueError("forbidden execution request")
    credential_terms = ("api_key", "api key", "secret_key", "secret key", "credential")
    if any(term in lowered for term in credential_terms):
        raise ValueError("forbidden credential request")
