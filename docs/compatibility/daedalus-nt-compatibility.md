# NT/Daedalus Compatibility Contract

## Current Version Pins

| Component | Version |
|---|---|
| Builder `nautilus_trader` | `1.227.0` (pyproject.toml) |
| Daedalus `nautilus_trader` | Verify against local reference |

## Compatibility Report

Builder produces a compatibility report via:
```bash
python3 -m packages.build_metadata.compatibility --daedalus-nt-version <VERSION>
```

Or via API:
```
GET /health/build
```

## Rules
- Builder must not import Daedalus directly
- Version mismatch blocks production/live-readiness claims
- Unknown Daedalus version blocks production/live-readiness claims
- Builder-only dev-demo can still run regardless

## Required External Evidence
For any adapter or live-readiness claim:
- DataTester evidence
- ExecTester evidence
- Reconciliation evidence
- Daedalus execution-boundary confirmation
