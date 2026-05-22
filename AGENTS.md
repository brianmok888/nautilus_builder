# AGENTS

## Repo reality
- Docs-only repo today. No `src/`, `tests/`, package manifest, CI workflow, or runnable build/test commands are present.
- `doc/` is the source-truth Builder doc set.
- `docs/superpowers/` is derived process output built from `doc/`.

## Read first
- `doc/README.md` for product identity.
- `doc/nautilus_builder_spec.md` and `doc/nautilus_builder_hardguards.md` for system/runtime truth.
- `doc/nautilus_builder_directory_architecture.md` and `doc/nautilus_builder_repo_dependency_architecture.md` for target layout and dependency boundaries.
- `docs/superpowers/` only after you understand `doc/`; it is interpretation, not primary truth.

## What agents get wrong here
- Paths like `apps/web`, `services/api`, `packages/*` are planned architecture in docs, not existing repo structure.
- Do not treat Nautilus-Daedalus as editable from this repo; Builder-side contracts only.
- Do not weaken the core rule that UX must not own runtime.
- Keep product names distinct: Nautilus Builder = product, Strategy Builder = one module, NautilusTrader = engine, Nautilus-Daedalus = live control system.

## Verified conventions
- `doc/` uses flat `nautilus_builder_*` snake_case filenames.
- `docs/superpowers/` uses dated `YYYY-MM-DD-...` filenames grouped by artifact type.
- This repo currently documents intended tests/verification gates, but does not contain runnable test infrastructure.

## Useful checks
```bash
git status
grep -R "Do not\|must not\|forbidden" doc
grep -R "Verification commands" docs/superpowers
```
