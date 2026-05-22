# Nautilus Builder — Existing Strategy Registry & Import Architecture

## 1. Purpose

The UX should be able to read existing strategies.

However, it must read them through a backend strategy registry, not by directly scanning source code from the browser or importing runtime modules.

Core rule:

```text
UX reads strategy metadata through backend APIs.
Backend owns strategy discovery, import, classification, and safety checks.
UX never edits live/runtime strategy code in place.
```

---

## 2. Strategy Sources

The Nautilus Builder should support three strategy source types.

### 2.1 Native Nautilus Builder Strategies

These are strategies created inside Nautilus Builder.

Canonical artifacts:

```text
StrategySpec
StrategySpecVersion
ValidationReport
CompileArtifact
BacktestResult
PromotionRequest
```

UX permissions:

```text
Draft   = editable
Testing = frozen once used in BacktestJob
Beta    = frozen
Final   = frozen
```

---

### 2.2 Existing Nautilus-Daedalus Strategies

These are existing Daedalus strategy shells, signal components, graph nodes, or strategy modules.

The UX may read them as catalog entries:

```text
strategy_id
name
description
source
kind
status
supported venues
supported instruments
supported timeframes
inputs/features
outputs
runtime boundary
test coverage
last modified
promotion eligibility
```

The UX should not directly edit these runtime files.

Safe workflow:

```text
Existing Daedalus strategy
  → read-only catalog entry
  → import/fork into StrategySpec if compatible
  → new Draft version in Nautilus Builder
  → validate
  → backtest
  → beta/shadow
  → final
```

---

### 2.3 Raw NautilusTrader Python Strategies

Raw NautilusTrader `Strategy` subclasses may be shown as external/imported strategies if discovered by a backend scanner.

But raw Python strategies are not automatically safe no-code strategies.

Safe workflow:

```text
Raw NautilusTrader strategy
  → backend metadata inspection
  → read-only UX catalog entry
  → optional manual import/wrap
  → new Draft StrategySpec only if importer can map it safely
```

If the importer cannot prove safety, show it as read-only only.

---

## 3. Strategy Registry Architecture

```text
Nautilus-Daedalus repo / Nautilus Builder DB / external NT strategies
  ↓
Backend Strategy Registry Scanner
  ↓
Strategy Catalog
  ↓
Nautilus Builder API
  ↓
UX Strategy Library
```

Recommended backend package:

```text
packages/strategy_registry/
  models.py
  strategy_manifest.py
  daedalus_strategy_scanner.py
  nautilus_strategy_scanner.py
  strategy_catalog.py
  import_to_strategy_spec.py
  safety_classifier.py
```

Recommended API routes:

```text
GET  /strategies
GET  /strategies/{strategy_id}
GET  /strategies/{strategy_id}/versions
GET  /external-strategies
GET  /external-strategies/daedalus
GET  /external-strategies/nautilus
POST /external-strategies/{external_id}/import-as-draft
POST /external-strategies/{external_id}/fork-as-draft
```

---

## 4. Strategy Manifest

Existing Daedalus strategies should expose a manifest file instead of relying only on source-code inspection.

Example:

```yaml
strategy_id: liquidation_cascade_reversal
source: daedalus
kind: signal_strategy
status: active
editable_in_ux: false

name: Liquidation Cascade Reversal
description: Uses liquidation pressure and order-book imbalance as confirmation/risk context.

inputs:
  - StateBundle.micro_signals.liquidation_pressure
  - StateBundle.micro_signals.l2_imbalance
  - StateBundle.regime

outputs:
  - StrategySignalPreview

supported:
  venues:
    - BINANCE
  asset_classes:
    - crypto_perp
  timeframes:
    - 1m
    - 5m

runtime_boundary:
  may_emit:
    - StrategySignalPreview
  may_create_trade_action: false
  may_submit_order: false
  may_call_execution_lane: false

import:
  can_import_as_strategy_spec: true
  import_profile: signal_preview_only
  default_stage: draft

tests:
  unit_test_path: tests/strategies/test_liquidation_cascade_reversal.py
  replay_test_path: tests/replay/test_liquidation_cascade_reversal.py
```

---

## 5. UX Strategy Library

The UX strategy library should show multiple sections:

```text
My Strategies
  native Nautilus Builder strategies

Imported Drafts
  strategies imported/forked into StrategySpec

Daedalus Catalog
  read-only existing Daedalus strategies

External Nautilus Strategies
  read-only or importable NT strategies

Final Releases
  frozen approved strategy releases
```

Each card should show:

```text
name
source
stage
version
editable/frozen status
last validation
last backtest
supported market/instrument
runtime boundary badge
```

Runtime boundary badges:

```text
Spec editable
Read-only catalog
Importable as Draft
Signal-preview only
Backtest-only
Final frozen
```

---

## 6. Import/Fork Rules

Importing an existing strategy never edits the original.

Correct:

```text
External strategy
  → import/fork
  → new StrategySpec Draft
  → new StrategySpecVersion 0.1.0-draft.1
```

Incorrect:

```text
UX edits existing Daedalus Python file directly
UX hot-patches production strategy module
UX changes live runtime code from browser
```

Imported strategy default state:

```text
stage: Draft
status: imported
validated: false
backtested: false
live_ready: false
source_ref: original strategy manifest/source
```

---

## 7. Safety Classification

Every discovered external strategy should be classified.

Suggested classifications:

```text
NATIVE_STRATEGY_SPEC
DAEDALUS_SIGNAL_STRATEGY
DAEDALUS_GATE_AWARE_STRATEGY
NAUTILUS_RAW_STRATEGY
UNKNOWN_RAW_CODE
UNSAFE_EXECUTION_STRATEGY
```

Safe UX handling:

```text
NATIVE_STRATEGY_SPEC
  editable according to lifecycle stage

DAEDALUS_SIGNAL_STRATEGY
  read-only catalog; import/fork allowed if manifest supports it

NAUTILUS_RAW_STRATEGY
  read-only catalog; manual wrapper/import only

UNKNOWN_RAW_CODE
  read-only metadata only

UNSAFE_EXECUTION_STRATEGY
  hidden from normal users or admin-only read-only
```

---

## 8. Backend Scanner Rules

The backend scanner may read local Daedalus source in development mode, but only backend code may do this.

The browser must never scan the local filesystem.

Development mode:

```text
DAEDALUS_REPO_PATH=../Nautilus-Daedalus
DAEDALUS_CONTRACT_MODE=local
DAEDALUS_EXECUTION_IMPORTS_ALLOWED=false
```

Scanner allowlist:

```text
contracts/
schemas/
strategy_manifests/
strategy_shells/
tests/fixtures/
```

Scanner denylist:

```text
runtime/execution/
live/
brokers/
credentials/
secrets/
.env
```

---

## 9. Hard Boundaries

The UX may:

```text
list existing strategies
open strategy detail page
view metadata/manifests
view validation/backtest history
import/fork compatible strategy as Draft
compare versions
request validation/backtest/promotion through API
```

The UX may not:

```text
directly scan Daedalus repo
directly import Python modules
directly edit runtime strategy files
directly modify live Daedalus strategy
directly create TradeAction
directly call submit_order
directly call run_execution_lane
```

---

## 10. Database Additions

Suggested tables:

```text
strategy_catalog_entries
external_strategy_sources
strategy_imports
strategy_source_refs
```

`strategy_catalog_entries` fields:

```text
catalog_id
strategy_id
name
source_type
source_ref
kind
status
editable_in_ux
importable_as_draft
runtime_boundary
supported_venues
supported_instruments
supported_timeframes
manifest_hash
last_scanned_at
created_at
updated_at
```

`strategy_imports` fields:

```text
import_id
external_strategy_id
new_strategy_spec_id
new_strategy_version_id
imported_by
import_mode
source_manifest_hash
created_at
```

---

## 11. Lifecycle Integration

Imported/forked strategies always start as Draft.

```text
External strategy
  → import/fork
  → 0.1.0-draft.1
  → validate
  → Testing
  → Beta
  → Final
```

Even if the source strategy is already live in Daedalus, the imported Nautilus Builder copy starts as Draft unless explicitly mapped to a known Final release artifact.

---

## 12. Acceptance Criteria

The existing strategy registry is complete when:

1. UX can list native Nautilus Builder strategies.
2. UX can list existing Daedalus strategies as read-only catalog entries.
3. UX can list raw Nautilus strategies as read-only external entries if scanner supports them.
4. UX can import/fork compatible external strategies as new Draft StrategySpec versions.
5. UX cannot edit live/runtime source files.
6. Backend scanner uses allowlist/denylist boundaries.
7. Imported strategies are unvalidated/not-backtested by default.
8. Existing strategies cannot become Final without lifecycle evidence.
9. Strategy registry does not import execution lane code.
10. No strategy registry path can call `submit_order`.

## 13. Existing Strategy Registry as Nautilus Builder Module

The Existing Strategy Registry is a module inside Nautilus Builder.

It is not the whole product.

Module responsibility:

```text
read existing strategies
classify source/safety
show read-only catalog
import/fork compatible strategies as Draft
```

It must still follow Nautilus Builder-wide lifecycle, dependency, and runtime boundary rules.
