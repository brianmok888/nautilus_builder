# Web application knowledge base

## OVERVIEW
Next.js 15, React 19 and Ant Design 6 operator UI; score 10, a separate TypeScript application.

## WHERE TO LOOK
| Task | Location | Notes |
|---|---|---|
| Routes and server/client composition | app/ | See app/AGENTS.md |
| Feature views | components/ | See components/AGENTS.md |
| HTTP calls and response types | lib/api.ts, lib/types.ts | No apiClient.ts compatibility module |
| Strategy spec helpers | lib/strategySpec.ts | Builder-side spec manipulation |
| ND display data flow | lib/tradehud/, components/tradehud/ | Feed, reducer, panels |
| Backend health | hooks/useHealthCheck.ts | UI health hook |
| Same-origin API proxy | middleware.ts | Backend destination and local token policy |
| Browser checks | e2e/, playwright.config.ts | Playwright configuration |
| Unit checks | vitest.config.mts | Colocated Vitest/jsdom tests |

## CONVENTIONS
- npm scripts in package.json own dev, build, typecheck, test and test:e2e.
- Run frontend commands from apps/web, not the root placeholder vitest.config.ts.
- TypeScript uses strict mode and disallows JS application files.
- Ordinary Builder HTTP calls use lib/api.ts; TradeHUD transport lives in lib/tradehud/replay-feed.ts.
- Python Pydantic contracts remain the reference for shared response shapes.
- middleware.ts supplies no-store HTML/API behavior; static assets retain their cache policy.
- Server bearer-token injection is limited to explicitly local environments.
- Keep credentials server-side; NEXT_PUBLIC variables are browser-visible configuration.

## ANTI-PATTERNS
- Do not add browser order submission or claim the UI owns execution authority.
- Do not expose BUILDER_API_TOKEN as NEXT_PUBLIC_BUILDER_API_TOKEN.
- Do not edit .next output or restore the deleted apiClient.ts abstraction.
- Do not describe Python tests/web as React execution coverage.

## COMMANDS
- npm run typecheck; npm run test; npm run build.
- npm run test:e2e selects Playwright; scripts/e2e_webui.sh is the repository's operational browser smoke path.
