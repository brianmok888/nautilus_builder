# Nautilus Builder — Builder Lifecycle & Versioning

## 1. Purpose

This document defines the development-style lifecycle for strategies created in Nautilus Builder.

The builder uses a staged release model:

```text
Draft → Testing → Beta → Final
```

Although this has four named stages, it follows a normal development pipeline:

```text
idea/design
  → test/research
  → beta/shadow validation
  → final/frozen release
```

If a strict three-stage model is needed later, `Testing` and `Beta` can be merged. For now, keeping them separate is safer.

---

## 2. Prime Rule

Lifecycle stage does not grant live trading authority.

Even a `Final` strategy may not directly submit orders.

For Nautilus-Daedalus live integration:

```text
Final StrategySpec
  → RuleGraphSignalStrategy
  → StrategySignalPreview
  → run_gate_engine
  → GateDecision
  → run_execution_lane
```

Only `run_execution_lane` may call `submit_order(...)`.

---

## 3. Lifecycle Stages

## Stage 1 — Draft

Draft is the idea/design stage.

Created by:

- user visual builder;
- AI strategy builder;
- imported spec;
- cloned previous strategy version.

Allowed actions:

- edit visual graph;
- edit StrategySpec;
- ask AI to revise;
- run schema validation;
- run hard-rule validation;
- save versions;
- clone/fork strategy.

Not allowed:

- shadow deployment;
- paper/live deployment;
- production promotion;
- direct execution;
- final result claims.

Required status labels:

```text
draft
unvalidated or validation_failed/passed
not_backtested
not_live_ready
```

Version examples:

```text
0.1.0-draft.1
0.1.0-draft.2
0.2.0-draft.1
```

Exit criteria to Testing:

- schema valid;
- hard-rule validator passed;
- adapter/instrument valid;
- risk block present;
- no forbidden execution blocks;
- no lookahead issues detected.

---

## Stage 2 — Testing

Testing is the controlled backtest/research stage.

Allowed actions:

- run NautilusTrader backtests;
- run parameter sweeps;
- run walk-forward tests;
- compare results;
- inspect logs/trades/fills;
- revise and create new draft/test versions.

Not allowed:

- live execution;
- direct TradeAction creation;
- production promotion without Beta review;
- modifying a tested version in place.

Required evidence:

- ValidationReport;
- CompileArtifact;
- BacktestResult;
- metrics;
- trade/fill logs;
- data range;
- adapter profile;
- instrument snapshot;
- compiler hash;
- worker image/version.

Version examples:

```text
0.2.0-test.1
0.2.0-test.2
0.3.0-test.1
```

Exit criteria to Beta:

- at least one successful backtest;
- result artifacts stored;
- no-lookahead check passed;
- out-of-sample or walk-forward plan exists;
- drawdown and risk limits reviewed;
- strategy version frozen for Beta candidate.

---

## Stage 3 — Beta

Beta is the shadow/paper candidate stage.

For Nautilus-Daedalus, Beta should default to shadow mode:

```text
RuleGraphSignalStrategy
  → StrategySignalPreview only
```

Allowed actions:

- run shadow signal deployment;
- compare shadow signals with live market;
- observe gate decisions;
- publish signal/gated-signal visibility;
- run paper/sim tests if explicitly enabled;
- collect drift and regime behavior.

Not allowed:

- direct live order submission;
- bypassing `run_gate_engine`;
- creating `TradeAction` directly;
- claiming production readiness without review;
- mutating the frozen Beta artifact.

Required evidence:

- shadow deployment record;
- signal trace;
- gate observation report;
- drift report;
- runtime stability report;
- user/manual review.

Version examples:

```text
0.3.0-beta.1
0.3.0-beta.2
1.0.0-beta.1
```

Exit criteria to Final:

- Beta artifact frozen;
- shadow/paper evidence reviewed;
- gate compatibility confirmed;
- no runtime boundary violations;
- risk guardian approval;
- manual final approval.

---

## Stage 4 — Final

Final is the frozen approved strategy release.

Final does not mean autonomous live execution.

It means:

- immutable StrategySpec version;
- immutable compiler artifact;
- approved validation evidence;
- approved backtest evidence;
- approved shadow/paper evidence;
- release notes;
- rollback path.

Allowed actions:

- use as production candidate;
- deploy into controlled Daedalus signal-preview path;
- compare against newer draft/testing/beta versions;
- retire/deprecate;
- patch through a new version.

Not allowed:

- editing in place;
- bypassing gate;
- bypassing execution lane;
- silent changes;
- changing adapter/instrument assumptions without new version;
- direct live submit.

Version examples:

```text
1.0.0
1.0.1
1.1.0
2.0.0
```

---

## 4. Versioning Model

Use SemVer-style release numbers with pre-release stage tags.

Format:

```text
MAJOR.MINOR.PATCH-STAGE.N
```

Examples:

```text
0.1.0-draft.1
0.1.0-draft.2
0.2.0-test.1
0.3.0-beta.1
1.0.0
1.0.1
```

Recommended meaning:

```text
MAJOR = major logic/model/risk change
MINOR = new indicator/rule/market config change
PATCH = small bugfix, parameter correction, metadata fix
STAGE.N = staged iteration counter
```

Final releases omit the stage suffix.

---

## 5. Immutability Rules

Editable:

```text
Draft versions
```

Frozen once used:

```text
Testing version used in a BacktestJob
Beta candidate
Final release
```

Never mutate historical tested versions.

Instead:

```text
clone → edit → create new version
```

---

## 6. Version State Machine

```text
DRAFT
  → VALIDATED_DRAFT
  → TESTING_CANDIDATE
  → TESTING_RUNNING
  → TESTING_PASSED
  → BETA_CANDIDATE
  → BETA_SHADOW_RUNNING
  → BETA_PASSED
  → FINAL_CANDIDATE
  → FINAL_RELEASED
```

Failure/side states:

```text
VALIDATION_FAILED
TESTING_FAILED
BETA_FAILED
FINAL_REJECTED
DEPRECATED
RETIRED
```

---

## 7. Promotion Requirements

Draft → Testing:

```text
schema valid
hard guards pass
adapter/instrument valid
risk rules present
no forbidden execution
```

Testing → Beta:

```text
successful backtest
result artifacts stored
no-lookahead passed
risk metrics reviewed
version frozen
```

Beta → Final:

```text
shadow/paper evidence
gate compatibility report
drift review
manual approval
release notes
rollback plan
```

---

## 8. Database Fields

Add to `strategy_spec_versions`:

```text
version
stage
stage_iteration
semver_major
semver_minor
semver_patch
is_frozen
parent_version_id
created_from
promotion_status
validation_report_id
last_backtest_result_id
beta_deployment_id
final_release_id
release_notes
deprecated_at
retired_at
```

Add to `promotion_requests`:

```text
from_stage
to_stage
requested_by
approved_by
approval_status
approval_notes
required_evidence
evidence_refs
created_at
approved_at
```

---

## 9. UX Requirements

Show lifecycle badge everywhere:

```text
Draft
Testing
Beta
Final
Deprecated
Retired
```

Recommended UX layout:

```text
Strategy Header:
  Name
  Current version
  Stage badge
  Frozen/editable status
  Last validation
  Last backtest
  Promotion button if eligible
```

Buttons by stage:

Draft:

```text
Validate
Run Backtest
Clone
Ask AI to Revise
Promote to Testing
```

Testing:

```text
Run Backtest
Run Parameter Sweep
Compare Results
Clone to Draft
Promote to Beta
```

Beta:

```text
Deploy Shadow
View Signal Trace
View Gate Observations
Clone to Draft
Promote to Final
```

Final:

```text
View Release
Deploy Candidate
Clone New Draft
Deprecate
Retire
```

---

## 10. AI Builder Rules

AI-generated strategies always start as Draft.

AI may suggest a promotion but cannot perform final approval.

AI output must include:

```text
strategy_id
version proposal
stage: draft
risk assumptions
explanation
known weaknesses
validation checklist
```

AI may not claim:

```text
production ready
safe for live
guaranteed profitable
approved
final
```

unless backend evidence and human approval exist.

---

## 11. Daedalus Boundary by Stage

Draft:

```text
No runtime deployment.
```

Testing:

```text
Nautilus backtest only.
```

Beta:

```text
Daedalus shadow/signal-preview only.
No TradeAction.
```

Final:

```text
Eligible for controlled Daedalus production candidate path.
Still no direct order submission.
Gate and execution lane remain mandatory.
```

---

## 12. Acceptance Criteria

Lifecycle implementation is complete when:

1. Every strategy has version and stage.
2. AI-created strategies start as Draft.
3. Draft can be edited.
4. Tested versions are frozen.
5. Beta versions are frozen.
6. Final versions are frozen.
7. Promotion requires evidence.
8. Browser/UX disconnect does not affect stage/job state.
9. Final does not bypass gate/execution lane.
10. Historical results link to exact immutable version.

## 13. Version Compatibility With NautilusTrader

Every StrategySpec version, BacktestResult, Beta deployment, and Final release should record the NautilusTrader version used.

Required metadata:

```text
nautilus_trader_version
strategy_lab_version
daedalus_contract_version
compiler_version
worker_image_version
```

Reason:

```text
Backtest behavior can change when engine, adapter, fill, or instrument semantics change.
Final strategy releases must be reproducible against the engine version they were validated on.
```

A NautilusTrader upgrade should trigger compatibility retesting before old Final strategies are considered valid on the new engine version.

## 14. Imported Existing Strategy Lifecycle

Existing strategies imported from Daedalus or raw NautilusTrader sources must enter Nautilus Builder as Draft.

```text
Existing strategy
  → import/fork
  → 0.1.0-draft.1
  → validation
  → Testing
  → Beta
  → Final
```

Even if the original source strategy is active in Daedalus, the imported Nautilus Builder copy is not automatically Final.

Default imported status:

```text
stage: Draft
validated: false
backtested: false
live_ready: false
source_ref: original catalog entry / manifest hash
```

Reason:

```text
Imported/forked strategies become new StrategySpec artifacts.
They must prove themselves through the Nautilus Builder lifecycle before release.
```

## 15. Nautilus Builder Lifecycle Scope

The Draft → Testing → Beta → Final lifecycle applies to strategy artifacts managed inside Nautilus Builder.

This lifecycle is managed by the Promotion Manager module.

Naming:

```text
Nautilus Builder = product
Promotion Manager = lifecycle owner
Strategy Builder = strategy authoring module
```
