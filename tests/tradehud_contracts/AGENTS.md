# TradeHUD contract-test knowledge base

## OVERVIEW
Executable ND payload and snapshot rules; retained distinct domain, structural score 4 before unmeasured symbols.

## WHERE TO LOOK
| Rule | Tests | Evidence |
|---|---|---|
| Fixture parsing | test_nd_fixture_loading.py | Recorded JSONL inputs |
| Missing versus zero | test_nd_normalizer_contracts.py | Numeric semantics and trade flags |
| Adapter contract | test_nd_redis_adapter_contracts.py | Parsing, snapshots, safe health |
| Model shapes | test_nd_snapshot_contracts.py | Snapshot payloads |
| Freshness | test_nd_freshness_contracts.py | SourceFreshnessMeta and staleness |
| Streaming | test_nd_stream_contracts.py, test_nd_sse_contracts.py | Event/SSE payload contracts |
| Read-only boundary | Local safety tests | No order authority or URL leakage |
| Broader Redis behavior | ../tradehud_redis/ | Sibling adapter contract suite |
| Shared recordings | ../fixtures/tradehud_nd_contracts/ | One event per JSONL line |

## CONVENTIONS
- Import packages.tradehud_contracts through the root conftest.py import setup.
- Name tests after the behavior being preserved.
- Distinguish adapter contract fakes from a connected Redis or ND runtime.
- Keep fixture changes compatible with scripts/tradehud_replay_nd_fixtures.py.
- The sibling tradehud_redis directory inherits tests/AGENTS.md, not this file.
- Run python3 -m pytest tests/tradehud_contracts tests/tradehud_redis -x -q.
- Replay with python3 scripts/tradehud_replay_nd_fixtures.py after recording changes.

## ANTI-PATTERNS
- Do not weaken missing-versus-zero assertions to accept malformed input.
- Do not assert raw connection URLs where sanitized output is required.
- Do not make these contract tests require live ND, real Redis or order credentials.
