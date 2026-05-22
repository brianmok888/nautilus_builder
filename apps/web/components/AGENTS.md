# AGENTS

## Scope
- `apps/web/components/` is placeholder UI surface only.
- These files currently encode authority boundaries and intended roles, not a runnable frontend.

## Conventions
- Keep component names aligned with product seams: `strategy-builder`, `ai-builder`, `terminal`.
- Strings/text in stubs should reinforce authority limits: draft-only, advisory-only, observational-only.
- Treat Python `packages/ui_contracts/*` as the current executable contract truth behind these UI concepts.

## Do not
- Do not imply a real React app shell exists; there is no `App.tsx`, `main.tsx`, or frontend manifest.
- Do not move runtime truth, shell access, or order authority into UI components.
- Do not let placeholder TSX drift away from the Python-backed contract tests in `tests/web/`.

## When this area grows
- Add deeper AGENTS only if these folders become real feature modules with state, hooks, or actual frontend runtime logic.
