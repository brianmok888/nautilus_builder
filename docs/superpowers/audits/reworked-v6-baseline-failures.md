# Reworked V6 Baseline Failure Report

**Date:** 2026-06-12
**Branch:** master (86cf623)

## Commands Run

| Command | Exit Code | Result |
|---------|-----------|--------|
| `python3 -m compileall -q packages services tests scripts` | 0 | Clean compile |
| `python3 -m pytest tests/ -q --tb=short` | 0 | 1424 passed, 1 skipped |
| `bash scripts/check_forbidden_authority.sh` | 0 | PASSED |
| `python3 scripts/check_release_version.py` | 0 | OK: All versions consistent at 0.5.0 |

## Confirmed Failures

**None.** All commands exit cleanly.

## Confirmed Gaps Requiring Enhancement (not failures, but improvement targets)

1. **Evidence Verifier too shallow** — only checks hash presence/length for artifact-backed types. Does not verify: hex format, expiry, source system, project scope, or actual artifact content.

2. **Artifact Store protocol drift** — `LocalJsonArtifactStore` has `put_json/get_json`, `S3ArtifactStore` has `put/get`. No unified protocol with `verify_ref`.

3. **Compiler v2 bundle not exported** — `compile_strategy_spec_bundle` exists and works but is not exported from `__init__.py`. Static scan is not integrated into bundle compilation.

4. **InMemoryEvidenceRepository missing `update_verification`** — PostgresEvidenceRepository has it but InMemory does not, creating interface mismatch.

5. **Evidence route `verify_evidence` handler saves instead of using `update_verification`** — bypasses the repository's explicit update method.

## Items Already Fixed (confirmed by this baseline)

- Evidence model/repository field alignment — no stale names
- Evidence API memory store — no global mutable dict
- Version check script — catches changelog drift
- Compiler handles both classic and microstructure families
- All tests pass with no failures
