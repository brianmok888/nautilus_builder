# TradeHUD client data knowledge base

## OVERVIEW
Normalized ND display state and feeds; retained distinct domain, measured score 6.

## WHERE TO LOOK
| Task | Module | Contract |
|---|---|---|
| Event and snapshot shapes | types.ts | Mirror Python TradeHUD contracts |
| State updates | reducer.ts | Pure reducer plus createInitialState |
| Derived panel data | selectors.ts | Order book, trades, lanes, ranges |
| Feed selection and transport | replay-feed.ts | createFeed and mock/snapshot/SSE modes |
| Synthetic feed | mock-feed.ts | Deterministic seeded mock data |
| Staleness status | freshness.ts | Age and freshness calculations |
| Rolling windows | ring-buffer.ts, heatmap-buffer.ts | Bounded buffers |
| Formatting | number-format.ts, time-format.ts | Display conversions |
| Feed behavior tests | sse-feed.test.ts | Tests replay-feed implementation; no sse-feed.ts module |

## CONVENTIONS
- Feed implementations dispatch TradeHudEvent values into the reducer.
- Preserve a pure state/event transition without fetches or transport side effects.
- Keep TS interfaces aligned with packages/tradehud_contracts/models.py.
- Preserve missing versus explicit zero through reduction and formatting.
- Bound histories through the provided buffer helpers.
- Freshness/provenance describe source evidence, not order execution readiness.
- Run npm run test -- lib/tradehud from apps/web for the colocated checks.

## ANTI-PATTERNS
- Do not parse raw ND Redis fields here; consume backend-normalized payloads.
- Do not introduce unbounded event arrays or an extra parallel feed implementation.
- Do not replace absent values with plausible market/account numbers.
- Do not interpret mock, snapshot or SSE mode alone as proof of a live ND connection.
