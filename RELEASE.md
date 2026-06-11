# Nautilus Builder — Release Process

## Version Scheme
## Current Release

**Version:** 0.1.0
**Status:** Unreleased / dev-demo
**Date:** 2026-06-11


Semantic Versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking API or config changes
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, security patches

Current: **v0.5.0** (hardening sprint complete)

## Release Checklist

### Pre-Release

- [ ] All tests pass: `python3 -m pytest tests/ -q --tb=short`
- [ ] Compile check clean: `python3 -m compileall -q packages services tests`
- [ ] Repo hygiene: `bash scripts/check_repo_hygiene.sh`
- [ ] Authority scan: `bash scripts/check_forbidden_authority.sh`
- [ ] Ruff lint clean: `ruff check packages services tests`
- [ ] CHANGELOG.md updated with release date and changes
- [ ] Version bumped in pyproject.toml and relevant __init__.py files
- [ ] .env.production.example reviewed for any new required variables
- [ ] Docker images build: `docker compose build`

### Release

- [ ] CI passes on the release commit
- [ ] Tag created: `git tag -a v0.5.0 -m "Release v0.5.0"`
- [ ] Tag pushed: `git push origin v0.5.0`
- [ ] Docker images pushed to registry (if applicable)

### Post-Release

- [ ] Verify deployment from docs alone
- [ ] Health endpoints responding
- [ ] No dev-token or NEXT_PUBLIC tokens in production
- [ ] Promotion ledger functional
- [ ] Artifact store accessible
- [ ] Audit trail writing

## Rollback Procedure

1. Identify the last known good tag: `git tag -l 'v*' | sort -V | tail -5`
2. Checkout and redeploy: `git checkout v0.4.0`
3. If database migration occurred, run manual rollback (see docs/operations.md)
4. Verify health endpoints

## Hotfix Process

1. Branch from the release tag: `git checkout -b hotfix/v0.5.1 v0.5.0`
2. Apply minimal fix with tests
3. Run full release checklist
4. Tag and deploy
5. Merge hotfix back to master

## Build Metadata

The API exposes build metadata at `GET /health/build`:

```json
{
  "version": "0.5.0",
  "commit": "abc123...",
  "build_time": "2026-06-07T12:00:00Z"
}
```

Set via environment: `GIT_COMMIT_SHA` and `BUILD_TIME`.


## v3 Gap Closure (2026-06-11)

### Closed items
- All legacy items removed (PostgresWorkflowRepository alias, backtest legacy hash, allow_legacy_fixture_refs, res_001 fixture fallback)
- Frontend API calls routed through canonical apiFetch; apiClient.ts deprecated
- AI prompt redaction before audit storage with secret pattern scanning
- Documentation alignment: readiness matrix, deployment runbooks, compatibility docs, deprecation inventory
- Full-system verification harness (scripts/verify_builder.py)

### Test counts
- 1332 Python tests (from 1306 baseline, +26)
- 138 frontend tests (from 131 baseline, +7)
- 0 legacy items remaining
