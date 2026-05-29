from __future__ import annotations

import warnings

from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import ProjectScopeError, UserProjectContext
from packages.promotions.service import PromotionService
from services.api.router import ApiResponse


def create_shadow_payload(
    payload: dict[str, object],
    *,
    context: UserProjectContext | None = None,
    artifact_store: LocalJsonArtifactStore | None = None,
    strict_evidence: bool = True,
) -> ApiResponse:
    target_evidence = payload.get("evidence_refs")
    if not isinstance(target_evidence, dict):
        return ApiResponse({"error": "promotion_evidence_missing", "details": ["evidence_refs"]}, status_code=422)

    allow_legacy = not strict_evidence
    if allow_legacy:
        warnings.warn(
            "allow_legacy_fixture_refs=True is deprecated; use strict evidence for all promotions",
            DeprecationWarning,
            stacklevel=2,
        )

    try:
        request = PromotionService(
            artifact_store=artifact_store if strict_evidence else None,
            context=context if strict_evidence else None,
            allow_legacy_fixture_refs=allow_legacy,
        ).create_shadow_request(
            strategy_version=str(payload.get("strategy_version", "")),
            compile_hash=str(payload.get("compile_hash", "")),
            gate_compatibility=payload.get("gate_compatibility") is True,
            evidence_refs=target_evidence,
        )
    except ProjectScopeError as exc:
        return ApiResponse({"error": "forbidden", "details": str(exc)}, status_code=403)
    except ValueError as exc:
        return ApiResponse({"error": "promotion_evidence_missing", "details": str(exc)}, status_code=422)
    return ApiResponse(request.model_dump(mode="json"), status_code=201)


def request_promotion_payload(payload: dict[str, object]) -> ApiResponse:
    target = str(payload.get("target", ""))
    try:
        request = PromotionService().request_builder_promotion(
            strategy_version_id=str(payload["strategy_version_id"]),
            result_id=str(payload["result_id"]),
            target=target,
        )
    except ValueError:
        return ApiResponse({"error": "unsupported_promotion_target", "target": target}, status_code=422)
    return ApiResponse(request, status_code=201)
