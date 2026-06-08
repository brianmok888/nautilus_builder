# Evidence Lifecycle Screenshots

This directory should contain screenshots demonstrating the full evidence lifecycle UI.

## Required Screenshots

When running the demo with `BUILDER_SEED_DEMO_STRATEGIES=1`, capture these screenshots:

### evidence-draft.png
- Strategy: `demo_draft`
- Shows: Draft lifecycle stage, validation missing/passed, compile/replay/promotion all missing
- Next action: Validate StrategySpec

### evidence-validation-failed.png
- Strategy: `demo_validation_failed`
- Shows: Validation failed stage, failed validation flag, blocking reason
- Next action: Fix validation errors

### evidence-compiled.png
- Strategy: `demo_compiled`
- Shows: Compile artifact hash/ref displayed, replay missing
- Next action: Run replay

### evidence-replay-passed.png
- Strategy: `demo_replay_passed`
- Shows: Replay report/artifact refs, compile hash, promotion missing
- Next action: Request promotion review

### evidence-replay-failed.png
- Strategy: `demo_replay_failed`
- Shows: Replay failed stage, error references, blocking reason
- Next action: Review replay errors

### evidence-promotion-requested.png
- Strategy: `demo_promotion_requested`
- Shows: Promotion ready state, full evidence chain
- Next action: Inspect evidence

### evidence-promotion-ready.png
- Strategy: `demo_promotion_ready`
- Shows: All evidence present, full audit timeline, execution profile pending
- Next action: Inspect evidence

## Screenshot Requirements

Each screenshot should show:
- Light UI theme
- Lifecycle panel (top section)
- Next action card
- Evidence grid with status tags
- Audit timeline
- Builder-only safety banner
- No live execution wording
