"""TDD tests for AuthTokenService bounded token store (C-01).

Ensures:
- Token store has a max capacity (LRU eviction when full)
- Tokens have a TTL and expired tokens are rejected
- revoke_token removes tokens
"""
from __future__ import annotations

import time
import pytest

from packages.auth.service import AuthTokenService


class TestTokenMaxCapacity:
    def test_tokens_beyond_max_are_evicted_oldest_first(self):
        """When max_tokens is set, oldest tokens should be evicted."""
        service = AuthTokenService(max_tokens=3)
        t1 = service.issue_token(user_id="u1", project_id="p1")
        t2 = service.issue_token(user_id="u2", project_id="p2")
        t3 = service.issue_token(user_id="u3", project_id="p3")
        # All 3 should be present
        assert service.verify_token(t1.token)
        assert service.verify_token(t2.token)
        assert service.verify_token(t3.token)

        # Adding a 4th should evict the oldest (t1)
        t4 = service.issue_token(user_id="u4", project_id="p4")
        with pytest.raises(Exception):  # InvalidAuthTokenError
            service.verify_token(t1.token)
        assert service.verify_token(t4.token)

    def test_default_max_tokens_is_unbounded(self):
        """Default behavior allows unlimited tokens."""
        service = AuthTokenService()
        for i in range(100):
            service.issue_token(user_id=f"u{i}", project_id="p")
        # All should still verify
        assert len(service._tokens) == 100


class TestTokenTTL:
    def test_expired_token_is_rejected(self):
        """Tokens older than ttl_seconds should be rejected."""
        service = AuthTokenService(ttl_seconds=0.1)
        token = service.issue_token(user_id="u1", project_id="p1")
        # Should work immediately
        assert service.verify_token(token.token)
        # Wait for expiry
        time.sleep(0.15)
        with pytest.raises(Exception):  # InvalidAuthTokenError
            service.verify_token(token.token)

    def test_fresh_token_within_ttl_is_accepted(self):
        service = AuthTokenService(ttl_seconds=60)
        token = service.issue_token(user_id="u1", project_id="p1")
        assert service.verify_token(token.token)


class TestRevokeToken:
    def test_revoke_token_removes_it(self):
        service = AuthTokenService()
        token = service.issue_token(user_id="u1", project_id="p1")
        service.revoke_token(token.token)
        with pytest.raises(Exception):
            service.verify_token(token.token)

    def test_revoke_nonexistent_token_is_noop(self):
        service = AuthTokenService()
        service.revoke_token("nonexistent_token")
