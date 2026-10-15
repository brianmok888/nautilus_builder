# Operational script knowledge base

## OVERVIEW
Directly invoked development, seed and verification tools; retained domain, structural score 2.

## WHERE TO LOOK
| Task | Scripts | Boundary |
|---|---|---|
| Local stack | run_dev.sh | API plus web development |
| Test entry | run_tests.sh | Selected backend test groups |
| Single backtest | run_backtest.py | Builder backtest tool |
| Browser smoke | e2e_webui.sh | Default operational rendered-UI check |
| Demo records | seed_builder_demo_data.py, seed_demo_evidence.py | Synthetic Builder data |
| TradeHUD fixtures | tradehud_replay_nd_fixtures.py | Local recorded-event replay |
| Redis seed | tradehud_seed_redis.py | Throwaway local Redis only |
| Schema application | apply_builder_migrations.py | infra/migrations SQL |
| Authority/secrets | check_forbidden_authority.sh, check_secrets.sh | Repository gates |
| Hygiene/docs | check_repo_hygiene.sh, check_docs_consistency.py | Consistency checks |
| Release checks | check_release_version.py, verify_all.sh | Version and aggregate checks |
| Production smoke | smoke_production.sh | Inspect configuration before invoking |

## CONVENTIONS
- Scripts are entry tools, not an importable domain API.
- Bash scripts commonly use set -euo pipefail; preserve meaningful exit codes.
- authority_scan_allowlist.txt exemptions need a concrete false-positive justification.
- Python tools run as python3 scripts/<name>.py with required optional dependencies installed.
- e2e_webui.sh drives agent-browser against an already running stack.
- Its E2E_BASE and E2E_SHOTS controls select the target and screenshot destination.
- Authenticated local smoke needs matching BUILDER_API_TOKEN configuration on API and Next middleware.

## ANTI-PATTERNS
- Do not point TradeHUD seed/replay tools at production Redis.
- Do not weaken authority or secret checks to turn a failing gate green.
- Do not add runtime-tree edits, order authority or embedded credentials to a helper script.
