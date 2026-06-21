"""P0-3 regression: pipeline compile failures must preserve a redacted root cause.

Previously `run_pipeline` caught the compiler exception with a bare
`except Exception:` and recorded only `PipelineStep(name="compile", status="failed")`,
dropping the exception type and message entirely. Operators could not tell whether a
failure came from spec validation, compiler assumptions, filesystem errors,
Nautilus API drift, or an unexpected runtime error. This test forces a compiler
exception and asserts the step preserves the error type and a redacted message,
and that secrets in the message are scrubbed.
"""
from __future__ import annotations

import sys
import types

import pytest

from packages.pipeline.service import run_pipeline


def _force_compile_to_raise(monkeypatch: pytest.MonkeyPatch, exc: BaseException) -> None:
    """Make run_pipeline's compile_strategy_spec call raise `exc`.

    service.py binds `compile_strategy_spec` into its own module namespace at
    import time, so patch the binding the service actually uses.
    """
    import packages.pipeline.service as service_mod

    def _boom(*args, **kwargs):
        raise exc

    monkeypatch.setattr(service_mod, "compile_strategy_spec", _boom)


def _valid_spec_payload() -> dict:
    """A payload that passes validate_strategy_spec so we reach the compile step."""
    from tests.strategy_spec.test_schema_valid import make_valid_spec

    return make_valid_spec()


def test_compile_failure_preserves_error_type_and_detail(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_spec_payload()
    _force_compile_to_raise(monkeypatch, RuntimeError("adapter profile missing required field 'venue'"))

    result = run_pipeline(payload)

    compile_step = next(s for s in result.steps if s.name == "compile")
    assert compile_step.status == "failed"
    assert compile_step.error_type == "RuntimeError"
    detail = compile_step.detail or ""
    assert "adapter profile missing required field" in detail


def test_compile_failure_redacts_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_spec_payload()
    secret_msg = (
        "connection failed for redis://default:s3cr3t-pw@redis.prod:6379/0 "
        "api_key=sk-live-9f8a7b6c5d bearer=Bearer abc123token"
    )
    _force_compile_to_raise(monkeypatch, ValueError(secret_msg))

    result = run_pipeline(payload)

    compile_step = next(s for s in result.steps if s.name == "compile")
    assert compile_step.status == "failed"
    assert compile_step.error_type == "ValueError"
    detail = compile_step.detail or ""
    # Root-cause text survives but secrets are scrubbed.
    assert "connection failed" in detail
    assert "s3cr3t-pw" not in detail
    assert "sk-live-9f8a7b6c5d" not in detail
    assert "abc123token" not in detail


def test_validate_failure_still_skips_compile_cleanly() -> None:
    """A validation failure must NOT attempt compile and must not populate detail."""
    result = run_pipeline({})  # empty payload fails validation
    statuses = {s.name: s.status for s in result.steps}
    assert statuses["validate"] == "failed"
    assert statuses["compile"] == "skipped"
    compile_step = next(s for s in result.steps if s.name == "compile")
    assert compile_step.detail is None
    assert compile_step.error_type is None


def test_pipeline_step_extra_forbid_still_enforced() -> None:
    """Adding detail/error_type must not loosen the extra='forbid' contract."""
    from packages.pipeline.service import PipelineStep
    from pydantic import ValidationError

    step = PipelineStep(name="compile", status="failed", detail="x", error_type="ValueError")
    assert step.detail == "x"
    assert step.error_type == "ValueError"
    with pytest.raises(ValidationError):
        PipelineStep(name="compile", status="failed", bogus_field=1)
