"""Evidence ledger models — typed evidence references with verification status."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ArtifactType(str, Enum):
    STRATEGY_SPEC = "strategy_spec"
    COMPILED_STRATEGY_IR = "compiled_strategy_ir"
    FEATURE_DEPENDENCY_GRAPH = "feature_dependency_graph"
    RISK_CONTRACT = "risk_contract"
    REPLAY_MANIFEST = "replay_manifest"
    BACKTEST_RESULT = "backtest_result"
    CATALOG_DATASET_MANIFEST = "catalog_dataset_manifest"
    DATA_TESTER_REPORT = "data_tester_report"
    EXEC_TESTER_REPORT = "exec_tester_report"
    RECONCILIATION_REPORT = "reconciliation_report"
    MANUAL_REVIEW = "manual_review"
    PROMOTION_REQUEST = "promotion_request"
    PROMOTION_DECISION = "promotion_decision"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    MISSING = "missing"
    SCOPE_MISMATCH = "scope_mismatch"
    SCHEMA_MISMATCH = "schema_mismatch"
    HASH_MISMATCH = "hash_mismatch"


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    strategy_lineage_id: str | None = None
    strategy_version_id: str | None = None
    artifact_type: ArtifactType
    source_system: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    sha256: str = ""
    schema_version: str = "evidence_v1"
    created_at: datetime | None = None
    producer: str = "builder"
    status: str = "active"
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verification_error: str | None = None
    expires_at: datetime | None = None
    metadata: dict = Field(default_factory=dict)
