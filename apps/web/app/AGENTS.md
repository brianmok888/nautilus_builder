# App Router knowledge base

## OVERVIEW
Route composition and server/client boundaries; score 9, a distinct Next.js routing domain.

## STRUCTURE
- builder/ and strategies/: Strategy Builder entry and strategy detail routes.
- backtests/: job pages with nested job-id routes.
- results/: result pages and nested result-id views.
- execution/ and config/: execution-lane display/configuration routes.
- pipeline/: pipeline workspace route.
- tradehud/: separate observational TradeHUD page.
- Root layout.tsx, page.tsx, loading.tsx and globals.css supply shared route presentation.

## WHERE TO LOOK
| Task | Location | Role |
|---|---|---|
| Shared document and shell | layout.tsx | Providers and application layout |
| Overview | page.tsx | Dashboard composition |
| Feature route | <feature>/page.tsx | Thin feature mount |
| Dynamic job route | backtests/[jobId]/ | Server loading plus client detail view |
| Dynamic result route | results/[resultId]/ | Result-specific composition |
| Strategy editing | builder/[strategyId]/ | Version/strategy context |
| Route regression checks | Colocated page.test.tsx files | Page loading and mounting contracts |

## CONVENTIONS
- Keep data loading and client interactivity explicit at each server/client boundary.
- Reuse components/<feature>/ rather than duplicating complete feature views in routes.
- Use lib/api.ts for backend contracts, including server-rendered reads.
- Carry route identifiers through to backend-owned records and errors.
- Keep the TradeHUD route on its feed/reducer display path.
- Keep asynchronous data and error display behavior aligned with the mounted client component.

## ANTI-PATTERNS
- Do not create a second routing framework or bypass existing shared layout providers.
- Do not embed backend credentials in client route props or public environment variables.
- Do not infer job completion from route navigation or a successful page render.
