# TradeHUD V0 — Hardening Pass

## Branch

- **Branch name:** `harden/tradehud-v0-pr-ready`
- **Worktree path:** `~/projects/nautilus_builder_tradehud_harden`
- **Base commit:** `0d39bf8` (origin/master)
- **V0 TradeHUD commits:** `7d67bb3`, `db18403` (merged via `--no-ff`)
- **Hardening commit:** this branch HEAD after hardening

## Scope

This hardening pass improves the TradeHUD V0 for merge review:

1. **Canvas performance** — replaced continuous `requestAnimationFrame` loop with dirty-render approach. Canvas only redraws when data changes, container resizes, or symbol changes. CPU stays idle when mock state is static.
2. **Bounded buffers** — added explicit hard limits for signal/gate/execution markers (200 each), confirmed existing limits for trades (500), liquidations (100), heatmap (360×160).
3. **Source freshness display** — 7 statuses (live, stale, missing, synthetic, true_zero, unavailable, unknown) are now visually distinct with unique CSS classes and labels.
4. **ND evidence semantics** — panels display explicit evidence labels: `NOT EXECUTABLE`, `APPROVAL EVIDENCE`, `RUNTIME-CONSUMED EVIDENCE ONLY`, `EXCHANGE/RUNTIME EVIDENCE`.
5. **Safety grep hardening** — expanded forbidden term scanning to cover exchange credential patterns, allowlisted safety-warning text in docstrings.
6. **Visual QA** — Playwright screenshot coverage at 4 viewport sizes with pre-screenshot assertions.
7. **Backend read-only verification** — confirmed all 3 endpoints are GET-only, no POST/PATCH/DELETE, provenance labeled `mock`/`synthetic`.

## Safety boundaries

**This TradeHUD is observational only.** It does not:
- Submit orders
- Create TradeAction
- Approve gates
- Hold exchange credentials
- Connect to Redis from browser
- Connect to PostgreSQL from browser
- Import Nautilus-Daedalus runtime

## Commands run

```bash
git worktree add -b harden/tradehud-v0-pr-ready ../nautilus_builder_tradehud_harden origin/master
git merge --no-ff feature/tradehud-webui-observability
npm run typecheck
npm run test
npm run build
python3 -m pytest tests/tradehud_contracts/ tests/web/test_tradehud_routes.py
npx playwright test e2e/tradehud.visual.spec.ts
```

## Known limitations

- Playwright E2E + visual screenshots require a running dev server (`npm run dev`)
- SSE feed mode is stub-only (snapshot + mock working)
- No live Redis/Postgres/Nautilus-Daedalus integration (by design — mock V0)
- Mobile viewport is best-effort; not a dedicated responsive design

## Next recommended branch

`feature/tradehud-live-gateway-sse` — live SSE gateway integration after V0 is visually and safely accepted.
