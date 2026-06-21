"""P2-5 regression: LLM transport must use explicit TLS verification + timeout.

The default transport used `urllib.request.urlopen(request, timeout=...)` with
implicit SSL verification and a Bandit S310 suppression. TLS verification must be
explicit (an ssl.SSLContext with check_hostname + verify_mode CERT_REQUIRED) and
the timeout must be forwarded.
"""
from __future__ import annotations

import ssl
from unittest.mock import MagicMock

import pytest


def _capture_urlopen_kwargs(monkeypatch: pytest.MonkeyPatch):
    captured: dict = {}

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{"id":"x","choices":[{"message":{"content":"{}"}}]}'

    def _fake_urlopen(request, timeout=None, context=None):
        captured["timeout"] = timeout
        captured["context"] = context
        return _FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    return captured


def test_transport_uses_explicit_ssl_context_with_verification(monkeypatch):
    captured = _capture_urlopen_kwargs(monkeypatch)
    from packages.ai_builder.provider import _urllib_json_transport

    _urllib_json_transport(
        url="https://api.example.test/v1/chat/completions",
        headers={"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
        payload={"model": "m", "messages": []},
        timeout_secs=12.5,
    )

    ctx = captured.get("context")
    assert isinstance(ctx, ssl.SSLContext), "transport must pass an explicit ssl.SSLContext"
    assert ctx.verify_mode == ssl.CERT_REQUIRED, "TLS certificate verification must be required"
    assert ctx.check_hostname is True, "TLS hostname checking must be enabled"


def test_transport_forwards_timeout(monkeypatch):
    captured = _capture_urlopen_kwargs(monkeypatch)
    from packages.ai_builder.provider import _urllib_json_transport

    _urllib_json_transport(
        url="https://api.example.test/v1/chat/completions",
        headers={"Authorization": "Bearer sk-test"},
        payload={"model": "m", "messages": []},
        timeout_secs=7.0,
    )

    assert captured.get("timeout") == 7.0
