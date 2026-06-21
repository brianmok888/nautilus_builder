"""Runtime safety guards for the TradeHUD ND fixture replay script.

The replay script writes synthetic ND TradeHUD contract fixtures into Redis
Streams. It is LOCAL DEVELOPMENT ONLY and must never run against production
infrastructure or a non-local Redis host. These tests lock the runtime guards:
host allowlist, environment guard, the scary override flag, and Redis URL
redaction in logs.
"""

from __future__ import annotations

import logging

import pytest

from scripts import tradehud_replay_nd_fixtures as replay


def test_is_local_redis_host_accepts_localhost_variants():
    assert replay.is_local_redis_host("redis://localhost:6379/0")
    assert replay.is_local_redis_host("redis://127.0.0.1:6379/0")
    assert replay.is_local_redis_host("redis://[::1]:6379/0")
    assert replay.is_local_redis_host("redis://:6379/0")  # no host == local default
    assert replay.is_local_redis_host("redis://localhost")


def test_is_local_redis_host_rejects_nonlocal_hosts():
    assert not replay.is_local_redis_host("redis://redis-host:6379/0")
    assert not replay.is_local_redis_host("redis://10.0.0.5:6379/0")
    assert not replay.is_local_redis_host("redis://prod-redis.example.com:6379")


def test_redact_redis_url_redacts_password():
    url = "redis://user:hunter2@redis-host:6379/0"
    redacted = replay.redact_redis_url(url)
    assert "hunter2" not in redacted
    assert "user" not in redacted  # userinfo is fully removed
    assert "redis-host" in redacted  # host is preserved for operator context


def test_redact_redis_url_preserves_non_secret_urls():
    url = "redis://127.0.0.1:6379/0"
    assert replay.redact_redis_url(url) == "redis://127.0.0.1:6379/0"
    assert replay.redact_redis_url("redis://localhost:6379") == "redis://localhost:6379"


def test_validate_local_dev_guard_accepts_local_url_in_local_env(monkeypatch):
    monkeypatch.delenv("BUILDER_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    # Should not raise / not exit.
    replay.validate_local_dev_guard("redis://127.0.0.1:6379/0", allow_nonlocal=False)


def test_validate_local_dev_guard_rejects_nonlocal_url_by_default(monkeypatch):
    monkeypatch.delenv("BUILDER_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    with pytest.raises(SystemExit) as exc_info:
        replay.validate_local_dev_guard(
            "redis://redis-host:6379/0", allow_nonlocal=False
        )
    assert exc_info.value.code != 0


def test_validate_local_dev_guard_override_allows_nonlocal(monkeypatch):
    """The explicit scary override flag must bypass the host allowlist."""
    monkeypatch.delenv("BUILDER_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    # Should not raise / not exit when override is explicitly requested.
    replay.validate_local_dev_guard(
        "redis://redis-host:6379/0", allow_nonlocal=True
    )


@pytest.mark.parametrize(
    "env_var",
    ["BUILDER_ENV", "APP_ENV", "ENVIRONMENT"],
)
@pytest.mark.parametrize(
    "env_val",
    ["production", "prod", "staging", "stage"],
)
def test_validate_local_dev_guard_rejects_production_envs(
    monkeypatch, env_var, env_val
):
    monkeypatch.setenv(env_var, env_val)
    with pytest.raises(SystemExit) as exc_info:
        replay.validate_local_dev_guard(
            "redis://127.0.0.1:6379/0", allow_nonlocal=False
        )
    assert exc_info.value.code != 0


def test_validate_local_dev_guard_override_does_not_bypass_production_env(monkeypatch):
    """The scary override bypasses the HOST allowlist only, NEVER the production-env guard."""
    monkeypatch.setenv("BUILDER_ENV", "production")
    with pytest.raises(SystemExit) as exc_info:
        replay.validate_local_dev_guard(
            "redis://127.0.0.1:6379/0", allow_nonlocal=True
        )
    assert exc_info.value.code != 0


def test_validate_local_dev_guard_dev_env_values_allowed(monkeypatch):
    """Explicit dev/local/test envs are permitted with a local host."""
    for val in ("local", "dev", "development", "test", "ci", ""):
        monkeypatch.setenv("BUILDER_ENV", val)
        replay.validate_local_dev_guard(
            "redis://127.0.0.1:6379/0", allow_nonlocal=False
        )


def test_main_logs_redacted_redis_url(monkeypatch, caplog):
    """main() must log a REDACTED Redis URL even when a password is present.

    Note: replay_fixtures is patched (so no real Redis/fixture work happens) and
    replay.asyncio.run is patched to a stub that drains the coroutine WITHOUT
    touching the global event-loop policy. This avoids polluting the asyncio loop
    state for later tests (the real asyncio.run would set/close the default
    loop, which can break other tests that call asyncio.get_event_loop()).
    """
    monkeypatch.setattr(
        "sys.argv",
        [
            "tradehud_replay_nd_fixtures.py",
            "--redis-url",
            "redis://user:supersecret@127.0.0.1:6379/0",
            "--fixture-dir",
            "tests/fixtures/tradehud_nd_contracts",
        ],
    )

    captured = {}

    async def fake_replay_fixtures(**kwargs):
        captured["redis_url"] = kwargs["redis_url"]

    monkeypatch.setattr(replay, "replay_fixtures", fake_replay_fixtures)

    def drain_without_event_loop(coro):
        # Exhaust the coroutine synchronously without creating/closing an event
        # loop, then return None like asyncio.run would.
        try:
            coro.send(None)
        except StopIteration:
            pass
        finally:
            coro.close()
        return None

    monkeypatch.setattr(replay.asyncio, "run", drain_without_event_loop)

    with caplog.at_level(logging.INFO):
        replay.main()

    # The real URL must still reach replay_fixtures unchanged.
    assert captured["redis_url"] == "redis://user:supersecret@127.0.0.1:6379/0"
    # But logs must never contain the secret.
    full_log = caplog.text
    assert "supersecret" not in full_log
    assert "REDIS" in full_log.upper() or "redis" in full_log.lower()
