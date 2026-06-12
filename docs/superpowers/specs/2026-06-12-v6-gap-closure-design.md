# V6 Gap-Closure Design — Nautilus Builder

**Date:** 2026-06-12
**Status:** Approved for implementation
**Branch:** master (direct)

## Context

After reviewing the v6 reworked master prompt against the actual codebase state post-v5 closure, the real remaining gaps are:

1. **Segment 01 — Baseline verification**: Force the repo to reveal current failure set. Most v6 gaps were already closed in v5, but this segment is still valuable as a confirmatory baseline.

2. **Segment 02 — Evidence Ledger Model/Repository**: ALREADY ALIGNED. No stale names remain. PostgresEvidenceRepository uses canonical EvidenceRef fields. No work needed beyond verification tests.

3. **Segment 03 — Evidence API repository injection**: ALREADY DONE. Routes use injected `repo` parameter. No global mutable `_evidence_store`. Production fails closed on in-memory. Enhance: add `update_verification` to `InMemoryEvidenceRepository` and route handler.

4. **Segment 04 — Evidence Verifier real artifact verification**: PARTIAL. Verifier only checks hash presence/length. Needs: expiry check, source_system validation, hex format validation, artifact store integration for real checksum verification.

5. **Segment 05 — Artifact Store protocol parity**: GAP EXISTS. `LocalJsonArtifactStore` uses `put_json/get_json` with `UserProjectContext`. `S3ArtifactStore` uses `put/get` with flat params. Need unified protocol with `put_json/get_json/verify_ref` on both.

6. **Segment 06 — Compiler v2 bundle authoritative**: PARTIAL. `compile_strategy_spec_bundle()` exists but `__init__.py` doesn't export it. Need to export and wire bundle into API routes. Static scan should be integrated into bundle compilation.

## Design Decisions

### D1: Unified ArtifactStoreProtocol
Add `put_json`, `get_json`, `verify_ref` to the protocol. Make `S3ArtifactStore` accept `UserProjectContext` in its methods and normalize to the same surface. Keep backward-compatible `put/get` on S3 store as internal methods.

### D2: Verifier Enhancement
Extend `verify_evidence_ref()` to accept optional `artifact_store` and `context` parameters. Add checks for:
- Hex format validation (lowercase hex only)
- Expiry (now vs expires_at)
- Source system allowlist
- Project scope mismatch
- Actual artifact checksum when store is available

### D3: Compiler Bundle Export
Export `compile_strategy_spec_bundle` and `FullArtifactBundle` from `__init__.py`. Add static scan step to bundle compilation. Wire bundle route into API.

### D4: InMemoryEvidenceRepository Enhancement
Add `update_verification` method to match PostgresEvidenceRepository interface. Add `list_by_project` with limit/offset pagination.

## Hard Rules Preserved
- Builder never owns live execution
- `execution_authority` always `False`
- No `submit_order` in production code
- No browser-exposed tokens in staging/production
- Deterministic hashes remain reproducible
- Missing data is not zero
- Production fails closed

## Test Strategy
Each segment uses TDD: write failing test first, then implement. All segments verified with:
```bash
python3 -m compileall -q packages services tests scripts
python3 -m pytest tests/ -q --tb=line
bash scripts/check_forbidden_authority.sh
```
