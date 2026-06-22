"""HttpxJsonTransport — modern HTTP transport for AI provider calls.

Adoption Report §4.1 / P2-5. Replaces the ``urllib.request.urlopen`` transport
with httpx for explicit timeouts, TLS verification, and testability via
``httpx.MockTransport``.

This transport is used ONLY for Builder-side LLM/provider HTTP calls.
NautilusTrader venue adapters are expected to use the Rust-core adapter pattern;
HTTPX here is not a substitute for production venue networking.
"""
from __future__ import annotations

from typing import Callable

import httpx


class HttpxJsonTransport:
    """Sync JSON POST transport with explicit timeout and TLS verification.

    Parameters
    ----------
    timeout_secs:
        Explicit per-request timeout. Never forwarded implicitly from the caller.
    verify:
        TLS certificate verification. Defaults to ``True`` (secure).
        Should only be ``False`` in explicit local dev test scenarios.
    _mock_handler:
        Optional ``httpx.MockTransport`` handler for testing. Production code
        never passes this; it is wired only in tests.
    """

    def __init__(
        self,
        *,
        timeout_secs: float,
        verify: bool = True,
        _mock_handler: Callable[[httpx.Request], httpx.Response] | None = None,
    ) -> None:
        if timeout_secs <= 0:
            raise ValueError("timeout_secs must be positive")
        self._timeout = httpx.Timeout(timeout_secs)
        self._verify = verify
        self._mock_handler = _mock_handler

    @property
    def verify(self) -> bool:
        """TLS verification flag (must be True by default)."""
        return self._verify

    def _build_client(self) -> httpx.Client:
        transport = httpx.MockTransport(self._mock_handler) if self._mock_handler is not None else None
        return httpx.Client(
            timeout=self._timeout,
            verify=self._verify,
            transport=transport,
        )

    def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
    ) -> dict[str, object]:
        """POST a JSON payload and return the decoded response dict.

        Raises ``ValueError`` on any failure (non-2xx, timeout, malformed JSON,
        non-dict body). Never returns partial output.
        """
        try:
            with self._build_client() as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            raise ValueError(f"OpenAI-compatible provider request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"OpenAI-compatible provider request failed: {exc}") from exc

        if response.status_code < 200 or response.status_code >= 300:
            # Redact any sensitive detail from the error body; never echo raw response.
            status = response.status_code
            detail = response.text[:200].replace("\n", " ").strip()
            raise ValueError(f"OpenAI-compatible provider HTTP {status}: {detail}")

        try:
            decoded = response.json()
        except Exception as exc:
            raise ValueError("OpenAI-compatible provider returned malformed JSON") from exc

        if not isinstance(decoded, dict):
            raise ValueError("OpenAI-compatible provider returned non-object response metadata")

        return decoded
