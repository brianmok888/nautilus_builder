"""Contract tests for HttpxJsonTransport (Adoption Report §4.1, P2-5).

Replaces the urllib.request.urlopen transport with httpx for explicit
timeouts, TLS verification, and better testability via httpx.MockTransport.
"""
from __future__ import annotations

import httpx
import pytest

from packages.ai_builder.http_transport import HttpxJsonTransport


def _ok_response(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})


def test_transport_post_json_returns_decoded_dict() -> None:
    transport = HttpxJsonTransport(timeout_secs=5.0)
    transport._mock_handler = _ok_response  # type: ignore[attr-defined]

    result = transport.post_json(
        url="https://test.example.com/v1/chat/completions",
        headers={"Authorization": "Bearer test-key"},
        payload={"model": "test", "messages": []},
    )

    assert isinstance(result, dict)
    assert "choices" in result


def test_transport_non_2xx_raises_structured_value_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="rate limited")

    transport = HttpxJsonTransport(timeout_secs=5.0, _mock_handler=handler)

    with pytest.raises(ValueError, match="provider"):
        transport.post_json(
            url="https://test.example.com/v1/chat/completions",
            headers={},
            payload={},
        )


def test_transport_timeout_is_enforced_and_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    transport = HttpxJsonTransport(timeout_secs=0.01, _mock_handler=handler)

    with pytest.raises(ValueError, match="timed out|timeout"):
        transport.post_json(
            url="https://test.example.com/v1/chat/completions",
            headers={},
            payload={},
        )


def test_transport_tls_verification_enabled_by_default() -> None:
    transport = HttpxJsonTransport(timeout_secs=5.0)
    # verify must default to True — never disabled implicitly.
    assert transport.verify is True


def test_transport_non_dict_response_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not", "a", "dict"])

    transport = HttpxJsonTransport(timeout_secs=5.0, _mock_handler=handler)

    with pytest.raises(ValueError, match="non-object|non-dict"):
        transport.post_json(
            url="https://test.example.com/v1/chat/completions",
            headers={},
            payload={},
        )


def test_transport_malformed_json_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"<<<not json>>>", headers={"content-type": "application/json"})

    transport = HttpxJsonTransport(timeout_secs=5.0, _mock_handler=handler)

    with pytest.raises(ValueError, match="provider"):
        transport.post_json(
            url="https://test.example.com/v1/chat/completions",
            headers={},
            payload={},
        )


def test_transport_does_not_leak_secrets_in_error_message() -> None:
    secret = "sk-super-secret-key-12345"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    transport = HttpxJsonTransport(timeout_secs=5.0, _mock_handler=handler)

    with pytest.raises(ValueError) as exc_info:
        transport.post_json(
            url="https://test.example.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {secret}"},
            payload={},
        )

    assert secret not in str(exc_info.value)
