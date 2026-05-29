# NautilusTrader Version Upgrade Checklist

Current pin: `nautilus_trader==1.223.0`
Daedalus pin: `nautilus_trader==1.223.0` (must upgrade in lockstep)

## Pre-upgrade checks

- [ ] Both `nautilus_builder` and `nautilus-daedalus` are on the same target version
- [ ] All adapter imports in `execution_lane/sessions.py` and `execution_lane/adapter_config_builders.py` compile against the new version
- [ ] `BacktestVenueConfig.trade_execution` is explicitly set (not relying on defaults)
- [ ] Run `packages/backtest_runner/runtime_check.py` and verify exact match

## v1.223.0 → v1.224.0 migration items

| Change | Impact | Action |
|--------|--------|--------|
| `fill_limit_at_touch` renamed to `fill_limit_inside_spread` | Builder doesn't use FillModel directly | Verify no references exist |
| Coinbase IntX adapter removed | Builder doesn't reference it | Verify no imports |
| `InstrumentProvider.load_ids_async`/`load_async` now have defaults | Builder doesn't implement custom providers | Verify adapter_config_builders still works |
| `InstrumentProvider.load_all_async` is the required override | Adapter builders don't implement providers | Verify |
| Binance Ed25519 env vars now raise ValueError | Builder uses standard HMAC keys | Verify credential slot validation |
| Hyperliquid `builder_fee_refresh_mins` config removed | Builder doesn't use Hyperliquid | Verify |

## v1.224.0 → v1.225.0 migration items

Check upstream changelog at https://github.com/nautechsystems/nautilus_trader/releases when upgrading past v1.224.

## v1.225.0 → v1.226.0 migration items

Check upstream changelog. Known additions in this range include `LiveNode` Rust runner improvements and adapter API refinements.

## Post-upgrade verification

```bash
python3 -m compileall -q packages services tests
python3 -m pytest tests/ -q --tb=short
cd apps/web && npm run typecheck && npm test && npm run build
```

## Updating the pin

1. Update `pyproject.toml` dependencies: `nautilus_trader==<NEW_VERSION>`
2. Update `packages/backtest_runner/engine_contract.py`: `NAUTILUS_TRADER_VERSION = "<NEW_VERSION>"`
3. Run `uv lock` or `pip install -e ".[test]"`
4. Run full verification suite above
5. Update this checklist with any new migration items discovered
