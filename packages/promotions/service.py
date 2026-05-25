from __future__ import annotations

from packages.artifact_store import LocalJsonArtifactStore
from packages.auth import UserProjectContext
from pydantic import ValidationError

from .models import PromotionEvidenceRefs, PromotionRequest


class PromotionService:
    def __init__(
        self,
        *,
        artifact_store: LocalJsonArtifactStore | None = None,
        context: UserProjectContext | None = None,
        allow_legacy_fixture_refs: bool = True,
    ) -> None:
        self.artifact_store = artifact_store
        self.context = context
        self.allow_legacy_fixture_refs = allow_legacy_fixture_refs

    def request_builder_promotion(
        self,
        *,
        strategy_version_id: str,
        result_id: str,
        target: str,
    ) -> dict[str, object]:
        if target not in {"shadow", "signal-preview"}:
            raise ValueError("unsupported_promotion_target")

        return {
            "strategy_version_id": strategy_version_id,
            "result_id": result_id,
            "target": target,
            "approval_state": "manual_approval_pending",
            "manual_approval_required": True,
            "may_submit_order": False,
            "may_create_trade_action": False,
            "mode": "builder_safe_promotion_request",
        }

    def create_shadow_request(
        self,
        *,
        strategy_version: str,
        compile_hash: str,
        gate_compatibility: bool,
        evidence_refs: dict[str, object],
    ) -> PromotionRequest:
        if not strategy_version.strip():
            raise ValueError("strategy version evidence is required")
        if not compile_hash.strip():
            raise ValueError("compile hash evidence is required")
        if gate_compatibility is not True:
            raise ValueError("gate compatibility evidence is required")
        evidence, checksums = self._validate_evidence(evidence_refs)

        return PromotionRequest(
            strategy_version=strategy_version,
            compile_hash=compile_hash,
            profile="signal_preview_only",
            may_submit_order=False,
            may_create_trade_action=False,
            gate_compatibility=True,
            manual_approval=False,
            evidence_refs=evidence,
            evidence_checksums=checksums,
        )

    def create_final_candidate(
        self,
        *,
        strategy_version: str,
        compile_hash: str,
        gate_compatibility: bool,
        manual_approval: bool,
        evidence_refs: dict[str, object],
    ) -> PromotionRequest:
        if not strategy_version.strip():
            raise ValueError("strategy version evidence is required")
        if not compile_hash.strip():
            raise ValueError("compile hash evidence is required")
        if not manual_approval:
            raise ValueError("manual approval is required")
        if gate_compatibility is not True:
            raise ValueError("gate compatibility evidence is required")
        evidence, checksums = self._validate_evidence(evidence_refs)

        return PromotionRequest(
            strategy_version=strategy_version,
            compile_hash=compile_hash,
            profile="signal_preview_only",
            may_submit_order=False,
            may_create_trade_action=False,
            gate_compatibility=True,
            manual_approval=True,
            evidence_refs=evidence,
            evidence_checksums=checksums,
        )

    def _validate_evidence(self, evidence_refs: dict[str, object]) -> tuple[dict[str, str], dict[str, str]]:
        try:
            evidence = PromotionEvidenceRefs.model_validate(evidence_refs)
        except ValidationError as exc:
            missing = [".".join(str(part) for part in error.get("loc", ())) for error in exc.errors()]
            raise ValueError(f"promotion evidence missing: {', '.join(missing)}") from exc

        evidence_payload = evidence.model_dump(mode="json")
        requires_artifacts = self.artifact_store is not None or self.context is not None or not self.allow_legacy_fixture_refs
        if not requires_artifacts:
            return evidence_payload, {}
        if self.artifact_store is None or self.context is None:
            raise ValueError("artifact store and auth context are required for scoped promotion evidence")

        checksums: dict[str, str] = {}
        for evidence_key, artifact_ref in evidence_payload.items():
            if not artifact_ref.startswith("artifact://builder/"):
                raise ValueError("scoped Builder artifact refs required")
            stored = self.artifact_store.get_json(context=self.context, artifact_ref=artifact_ref)
            actual_type = stored.record.artifact_type
            if actual_type != evidence_key:
                raise ValueError(
                    f"artifact type mismatch: {evidence_key} expected {evidence_key}, got {actual_type}"
                )
            checksums[evidence_key] = stored.record.checksum_sha256
        return evidence_payload, checksums
