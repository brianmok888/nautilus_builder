Fix all HIGH-priority review findings from the 2026-05-28 deep review, then continue work to make the web app production-beta-ready.

HIGH-priority fixes:
1. HIGH-1: Explicitly set trade_execution in config_builder.py; add NT version alignment test
2. HIGH-2: Rename TestJobRecord/TestResultRecord to WorkflowJobRecord/WorkflowResultRecord
3. HIGH-3: Flip allow_legacy_fixture_refs default to False; add deprecation warning

Production beta readiness:
4. Wire adapter_registry to execution_lane for multi-adapter support
5. Add rate limiting middleware to AI builder routes
6. Add typed error hierarchy for builder service errors
7. Ensure frontend builds cleanly and add DESIGN.md reference to README
8. Run full verification suite and confirm clean state
