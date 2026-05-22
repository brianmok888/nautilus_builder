# AGENTS

## Scope
- `docs/superpowers/` is derived process output, not primary product truth.
- Every change here should trace back to `doc/` inputs or an approved spec in `specs/`.

## Read order
- `specs/` first for approved intent.
- `plans/` for execution sequence.
- `audits/` for why a rewrite/change exists.
- `designs/` for operating contract.
- `prompts/` last for final agent-facing execution text.

## Conventions
- Use dated filenames: `YYYY-MM-DD-<topic>.md`.
- Keep docs short, explicit, and evidence-oriented.
- If guidance is OpenCode-specific, provide a generic-agent equivalent when it changes execution.

## Do not
- Do not outrank `doc/` source truth with derived prose.
- Do not introduce cross-repo implementation requirements.
- Do not leave recommendations unverifiable; include evidence/verification expectations.
- Do not repeat root-level repo facts in every derived file.
