# AGENTS — scripts

Operational, seed, verify, and demo scripts. Not part of the importable package surface — invoked directly.

## Scope
- **Run/dev**: `run_dev.sh` (local API + web dev), `run_tests.sh` (pytest slice), `run_backtest.py` (single backtest), `e2e_webui.sh` (agent-browser e2e web UI test — DEFAULT for web UI testing).
- **Seed/demo**: `seed_builder_demo_data.py`, `seed_demo_evidence.py` (demo strategies + evidence artifacts).
- **TradeHUD (LOCAL DEV ONLY)**: `tradehud_seed_redis.py` (seed Redis Streams for the adapter), `tradehud_replay_nd_fixtures.py` (replay `tests/fixtures/tradehud_nd_contracts/*.jsonl` through normalizer+adapter). Both are local-development only — never run against production Redis.
- **Hygiene/checks**: `check_docs_consistency.py`, `check_forbidden_authority.sh` (+ `authority_scan_allowlist.txt`), `check_repo_hygiene.sh`, `check_secrets.sh`, `check_release_version.py`, `verify_all.sh`, `smoke_production.sh`.
- **Migrations**: `apply_builder_migrations.py` (apply `infra/migrations/`).

## Conventions
- Bash scripts use `set -euo pipefail` style; check before assuming lenient mode.
- Hygiene scripts are referenced by CI/pre-commit — keep their exit codes meaningful (0 = clean).
- `authority_scan_allowlist.txt` lists substrings that the forbidden-authority scan should treat as false positives; extend it only with a real justification.
- Python scripts are runnable via `python3 scripts/<name>.py` (no package install required) unless they import optional deps.

## Web UI e2e testing — agent-browser is the default tool
- `scripts/e2e_webui.sh` drives a real headless Chrome via [agent-browser](https://www.npmjs.com/package/agent-browser) (`npm i -g agent-browser`) against the running stack.
- It is the **default tool for web UI e2e tests** in this repo. Prefer it over ad-hoc curl for anything that needs to assert rendered UI, navigation, or the read-only/advisory safety contract in the browser.
- What it asserts: stack reachability, every main route renders, no route exposes order-submission UI, execution-lane safety switches (`may_submit_order=false`, `credential_inputs_allowed=false`, disabled runtime actions), frontend<->backend proxy is wired, and client-side routing works.
- Requires the stack up (`scripts/run_dev.sh`) with a matching `BUILDER_API_TOKEN` on both the API and the Next.js middleware (the middleware injects the bearer token in local mode).
- Usage: `bash scripts/e2e_webui.sh` (override base with `E2E_BASE`, screenshots with `E2E_SHOTS`). Exit code = failure count.

## Anti-patterns (THIS PROJECT)
- Never run `tradehud_seed_redis.py` / `tradehud_replay_nd_fixtures.py` against anything but a local throwaway Redis.
- Never weaken `check_forbidden_authority.sh` / `check_secrets.sh` to make CI green.
- Never add a script that grants the Builder order authority or edits Nautilus-Daedalus.
- Never commit real secrets; `check_secrets.sh` is the last line of defense, not the first.

## Verification
```bash
bash scripts/verify_all.sh
bash scripts/check_repo_hygiene.sh
python3 scripts/tradehud_replay_nd_fixtures.py
bash scripts/e2e_webui.sh
```
