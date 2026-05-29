Production beta readiness for Nautilus Builder web app.

Remaining MEDIUM-priority items to resolve:
1. MEDIUM-2: Add runtime guard to NativeTradingNodeSessionRunner blocking from API event loop
2. MEDIUM-3: Add execution lane persistence seam (serialize to disk for recovery)
3. MEDIUM-4: Add typed Pydantic model for NautilusTradingNodeRuntimePlan config_contract
4. MEDIUM-7: Install Playwright browsers and ensure E2E tests can run

Frontend production polish:
5. Add loading states and error boundaries to all page components
6. Add responsive layout improvements for mobile/tablet viewports
7. Ensure all API-backed components handle 429/422/404 gracefully
8. Add production health check integration to the dashboard
9. Final verification: full test suite + frontend build + typecheck clean
