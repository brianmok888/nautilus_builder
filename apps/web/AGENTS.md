# AGENTS

## Scope
- `apps/web/` is the operator-facing Next.js 15 frontend.
- Stack: React 19, Ant Design 6, TypeScript 5 (strict), Vitest, Playwright.
- This is a **display-only advisory layer**. Runtime, order, and credential authority live in the Python backend.

## Structure
```
apps/web/
├── app/                  # Next.js App Router pages
│   ├── backtests/        # Backtest job detail + status
│   ├── builder/          # Strategy Builder workspace
│   ├── config/           # Execution lane config
│   ├── execution/        # Execution lane status
│   ├── results/          # Backtest results/reports
│   └── strategies/       # Strategy list/detail
├── components/           # UI components (see components/AGENTS.md)
├── hooks/                # React hooks (useHealthCheck, etc.)
├── lib/                  # API client, types, strategySpec helpers
├── e2e/                  # Playwright E2E specs
└── middleware.ts         # Cache-Control: no-store for VM demo safety
```

## WHERE TO LOOK
| Task                | Location                              |
|---------------------|---------------------------------------|
| Add a page route    | `app/<route>/page.tsx`                |
| Add/edit a component| `components/<domain>/`                |
| API client calls    | `lib/api.ts`, `lib/apiClient.ts`      |
| Shared types        | `lib/types.ts`                        |
| Strategy spec logic | `lib/strategySpec.ts`                 |
| E2E tests           | `e2e/builder-shell.spec.ts`           |
| Unit tests          | `lib/*.test.ts`, `components/**/*.test.tsx` |

## Conventions
- Pages are thin shells that mount components from `components/`.
- `lib/api.ts` is the sole API client — never call `fetch` directly in components.
- `lib/types.ts` holds shared TS interfaces; keep them aligned with Python Pydantic models.
- Components use Ant Design primitives; avoid introducing new UI libraries.
- `middleware.ts` forces no-store caching for all HTML — do not remove.

## Anti-patterns (THIS PROJECT)
- Never embed API keys, exchange credentials, or `TradeAction` calls in frontend code.
- Never import from `node_modules/antd/` internals — use the public API only.
- Never bypass `lib/api.ts` for backend calls.
- Never treat the frontend as runtime authority — it displays backend state, it does not own it.
- Never add state management libraries (Redux, Zustand) without explicit agreement.
- Components must reinforce authority limits in visible text: draft-only, advisory-only, observational-only.

## Commands
```bash
npm run dev          # Next.js dev server
npm run build        # Production build
npm run typecheck    # tsc --noEmit
npm run test         # Vitest unit tests
npm run test:e2e     # Playwright E2E
```

## Notes
- `tsconfig.json` has `strict: true` and `allowJs: false` — no JS files allowed.
- The `.next/` build output is gitignored but present locally; do not edit it.
- `e2e/` uses Playwright, not Vitest — they have separate configs.
- `lib/` unit tests (`*.test.ts`) run under Vitest with jsdom.
- Python-backed UI contract truth lives in `packages/ui_contracts/` and `tests/web/`.
