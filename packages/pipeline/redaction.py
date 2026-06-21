"""Redaction helpers for pipeline error messages.

Operators need root-cause text to diagnose compile failures, but exception
messages can transitively contain secrets (API keys, bearer tokens, Redis URLs
with passwords, credential-like values). These helpers scrub credential-shaped
substrings while preserving the diagnostic message structure.
"""
from __future__ import annotations

import re

# Order matters: scrub URL-embedded credentials before generic token patterns.
_REDIS_URL_RE = re.compile(r"(redis(?:s)?://)([^@\s:/]+)(:[^@\s:/]*)?@")
_BEARER_RE = re.compile(r"(bearer\s+)([A-Za-z0-9._\-=/+]+)", re.IGNORECASE)
_API_KEY_RE = re.compile(
    r"(api[_-]?key(?:=|:\s*))([A-Za-z0-9][A-Za-z0-9._\-]{6,})", re.IGNORECASE
)
_SECRET_KV_RE = re.compile(
    r"(password|passwd|secret|token|passphrase|apikey|api_secret)(=|:\s*)([^\s,;'\"]+)",
    re.IGNORECASE,
)


def redact_error_message(message: str) -> str:
    """Return a diagnostic-safe copy of ``message`` with secrets scrubbed.

    Replaces credential-like substrings (Redis URL passwords, bearer tokens,
    api_key/password/secret/token assignments) with a placeholder. Non-credential
    text, including the surrounding words that give operators context, is
    preserved.
    """
    if not message:
        return ""
    redacted = _REDIS_URL_RE.sub(lambda m: f"{m.group(1)}***:***@", message)
    redacted = _BEARER_RE.sub(r"\1***", redacted)
    redacted = _API_KEY_RE.sub(r"\1***", redacted)
    redacted = _SECRET_KV_RE.sub(r"\1\2***", redacted)
    return redacted
