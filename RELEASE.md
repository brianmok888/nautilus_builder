# Nautilus Builder — Release Process

## Version Scheme

Semantic Versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking API or config changes
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, security patches

## Current Release

**Version:** 0.5.0
**Status:** Unreleased / dev-demo
**Date:** 2026-06-11

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
- [ ] Tag created: `git tag -a v<CURRENT_TAG> -m "Release v<CURRENT_TAG>"`
- [ ] Tag pushed: `git push origin v<CURRENT_TAG>`
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
2. Checkout and redeploy: `git checkout v<PREVIOUS_TAG>`
3. If database migration occurred, run manual rollback (see docs/operations.md)
4. Verify health endpoints

## Hotfix Process

1. Branch from the release tag: `git checkout -b hotfix/v<NEXT_PATCH> v0.5.0`
2. Apply minimal fix with tests
3. Run full release checklist
4. Tag and deploy
5. Merge hotfix back to master

## Build Metadata

The API exposes build metadata at `GET /health/build`:

```json
{
  "version": "0.5.0",
  "git_commit": "abc123...",
  "build_time": "2026-06-07T12:00:00Z"
}
```

Set via environment: `GIT_COMMIT_SHA` and `BUILD_TIME`.

## Changelog

### v0.5.0 (2026-06-11)

- Gap Closure v3: removed all legacy items, fixed M-03/M-06, added docs alignment
- Gap Closure v2: 17 segments, readiness API, feature registry, evidence policy
- Gap Closure v1: 15 segments, StrategySpec v2, compiler IR, evidence ledger

### v0.4.0 (2026-06-08)

- Segment 1-5 closure: credential safety, API exposure, rate limiting, audit, artifact readiness

### v0.1.0 (2026-05-22)

- Initial Builder foundation
