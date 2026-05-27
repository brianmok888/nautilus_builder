# Design

## Source of truth
- Status: Draft
- Last refreshed: 2026-05-27
- Primary product surfaces: Strategy Builder, Backtest Center, Execution Lane / Config, Strategy records, Results / Reports.
- Evidence reviewed:
  - `AGENTS.md`
  - `doc/README.md`
  - `doc/nautilus_builder_spec.md`
  - `doc/nautilus_builder_hardguards.md`
  - `structure.md`, `findings.md`, `handguard.md`
  - `apps/web/app/layout.tsx`, `apps/web/app/page.tsx`, `apps/web/app/config/page.tsx`, `apps/web/app/backtests/[jobId]/page.tsx`
  - `apps/web/components/shell/OperatorAppShell.tsx`
  - `apps/web/components/dashboard/BuilderDashboard.tsx`
  - `apps/web/components/config/*`, `apps/web/components/backtests/*`, `apps/web/components/strategy-builder/*`
  - Local Playwright screenshots under `/tmp/nb-ui-status/*-polished3-viewport.png`

## Brand
- Personality: serious trading-ops command center, compact, safety-forward, technical but not raw scaffold text.
- Trust signals: explicit no-browser-authority badges, backend-owned worker/API language, manual promotion gates, clear Strategy Builder -> Backtest Center -> Execution Lane separation.
- Avoid: consumer gamification, live-trading affordances in the browser, hidden credentials, terminal-as-shell styling for non-terminal pages, oversized typography that makes the workflow feel unfinished.

## Product goals
- Goals:
  - Let an operator start with natural language and produce a guarded StrategySpec draft.
  - Make BacktestNode evidence generation visibly separate from paper/live execution.
  - Make Execution Lane controls clearly backend-owned and server-credential-slot based.
  - Present the app as a usable MVP rather than a text-only contract demo.
- Non-goals:
  - Browser-held API keys or exchange credentials.
  - Direct browser order submission, `TradeAction`, shell access, or worker handle ownership.
  - Merging strategy drafting, backtesting, and paper/live execution into one unsafe action.
- Success signals:
  - Sidebar navigation remains stable and compact.
  - Three-lane workflow is visible above the fold.
  - Forms render full-width and readable in the available card space.
  - Backtest/execution pages show status, evidence, and guardrails without looking like raw text dumps.

## Personas and jobs
- Primary personas:
  - Quant/operator validating strategy ideas before promotion.
  - Developer/operator checking backend contract health.
- User jobs:
  - Describe a strategy in plain language.
  - Inspect and validate generated StrategySpec output.
  - Select strategy/data/venue/instrument/range and run BacktestNode replay.
  - Review artifacts/results and manually promote.
  - Configure model roles and paper/live execution lane visibility without browser secrets.
- Key contexts of use: local/dev VM, operator desktop browser, backend-connected but safety-limited UI.

## Information architecture
- Primary navigation: fixed left operator sidebar with Strategy Builder, Backtest Center, Execution Lane, Strategy records, Results / Reports.
- Core routes/screens:
  - `/`: command-center dashboard plus tabbed Strategy Builder / Backtest Center / Execution Lane surfaces.
  - `/backtests/[jobId]`: BacktestNode job status, run configuration, event stream, artifacts, cancel request.
  - `/config`: OpenAI-compatible model role config and execution-lane paper/live feature controls.
  - `/strategies`, `/strategies/[strategyId]`, `/builder/[strategyId]`: strategy records/detail/editing.
  - `/results/[resultId]`: observational backtest result/report surface.
- Content hierarchy: lane guardrail -> primary action -> contract/status evidence -> advanced JSON/artifact details.

## Design principles
- Principle 1: Make the safe path obvious. Use lane labels and status chips before advanced contract payloads.
- Principle 2: Keep density high but readable. Compact fonts, cards, and forms are preferred over oversized marketing hero sections.
- Principle 3: Every trading-control surface must show the authority boundary near the action.
- Tradeoffs: The UI may expose some backend contract vocabulary for auditability, but normal users should see clear lane/actions first and IDs/artifacts second.

## Visual language
- Color: dark navy base with cyan for Builder/backtest affordances, green for safety/validity, amber for manual gates, red only for dangerous/blocked states.
- Typography: system sans for app UI; monospace only for code, JSON previews, and explicit terminal/event payload snippets.
- Spacing/layout rhythm: compact 8-12px card rhythm, 260px sidebar, sticky top status header, two/three-column cards on desktop, single column on small screens.
- Shape/radius/elevation: rounded cards and pills with subtle borders; avoid heavy shadows except main surface separation.
- Motion: minimal hover translation only; no distracting live-trading animations.
- Imagery/iconography: Ant Design icons may label lanes; no decorative images required.

## Components
- Existing components to reuse:
  - `OperatorAppShell`
  - `BuilderDashboard`
  - `AiStrategyCopilot`
  - `StrategyBuilderWorkspace`
  - `BacktestLaunchPanel`
  - `BacktestJobClient`
  - `ExecutionLaneFeaturePanel`
  - `ModelConfigTabs`
- New/changed components:
  - CSS-level AntD fallback styling in `apps/web/app/globals.css` for shell/grid/forms/selects/cards/tags/descriptions.
  - Shell navigation cleanup in `OperatorAppShell`.
- Variants and states: normal, selected lane, loading/degraded backend, validation error, warning/manual gate, success/saved, disabled/no-authority.
- Token/component ownership: CSS variables in `apps/web/app/globals.css` are the current repo-local design token source.

## Accessibility
- Target standard: practical WCAG 2.1 AA intent for text contrast, keyboard navigation, and visible focus.
- Keyboard/focus behavior: sidebar links and tab buttons must remain keyboard reachable; form controls need visible labels.
- Contrast/readability: dark surfaces must preserve readable text and muted text contrast.
- Screen-reader semantics: navigation has `aria-label`; route sections should keep meaningful headings and form labels.
- Reduced motion and sensory considerations: avoid required animation; hover motion is decorative and nonessential.

## Responsive behavior
- Supported breakpoints/devices: desktop-first operator UI; tablet/mobile should stack sidebar/content safely.
- Layout adaptations: sidebar becomes top block below `991px`; grid cards collapse to one column.
- Touch/hover differences: cards can be clickable, but primary tabs/buttons must also expose the same actions.

## Interaction states
- Loading: use status text/alerts, keep controls disabled only when backend action is pending.
- Empty: show concise empty state plus next safe action.
- Error: show clear API/proxy/backend error without raw HTML/JSON parse noise.
- Success: show saved/queued/started state with backend IDs as secondary evidence.
- Disabled: explain guardrail reason, especially no live order authority or missing manual approval.
- Offline/slow network: degrade to observational fallback and label backend unavailable.

## Content voice
- Tone: operator-readable, concise, safety-forward.
- Terminology: Strategy Builder, StrategySpec, Backtest Center, BacktestNode, Execution Lane, TradingNode, manual promotion, backend-owned.
- Microcopy rules:
  - Say “server-side credential slot,” not “enter exchange key in browser.”
  - Say “request cancel,” not “kill worker.”
  - Say “paper/live gated,” not “start live trading” unless manual/live approval is explicit.

## Implementation constraints
- Framework/styling system: Next.js App Router, React, Ant Design v6, global CSS fallbacks.
- Design-token constraints: no new design system dependency for the current polish pass.
- Performance constraints: keep CSS simple; avoid client-only layout libraries.
- Compatibility constraints: AntD v6 component DOM currently requires local fallback CSS for stable dev/SSR rendering.
- Test/screenshot expectations:
  - Capture Playwright screenshots for `/`, `/config`, and `/backtests/bt_job_001` after visible shell changes.
  - Run `npm run typecheck`, `npm test`, `npm run build`, and `npm run test:e2e` for web changes when Playwright browsers are available.

## Open questions
- [ ] Should the config route split model roles and execution lane into separate top-level routes once both mature? / owner: product / impact: navigation complexity.
- [ ] Which chart library should own result/equity visualizations? / owner: frontend / impact: results polish and dependency policy.
- [ ] What exact NautilusTrader version will be the pinned backend engine target? / owner: backend / impact: UI readiness labels and engine-smoke claims.
