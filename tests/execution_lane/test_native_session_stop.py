"""P1-5 regression: NativeTradingNodeSessionRunner.stop must be idempotent and
report terminal-state guarantees.

Previously stop() did `node, thread = self._sessions.pop(session_id)` (KeyError
on unknown/double stop), unconditionally called node.dispose() even if the thread
was still alive after the join timeout, and emitted no STOP_TIMEOUT signal. This
test exercises the four lifecycle paths with fakes.
"""
from __future__ import annotations

import threading
import time

import pytest

from packages.execution_lane.sessions import NativeTradingNodeSessionRunner


class _FakeNode:
    def __init__(self, *, hang: bool = False) -> None:
        self.hang = hang
        self.stopped = False
        self.disposed = False

    def stop(self) -> None:
        self.stopped = True

    def dispose(self) -> None:
        if self.hang:
            pytest.fail("dispose() must not be called while the worker thread is still alive")
        self.disposed = True


def _hung_thread() -> threading.Thread:
    """A thread that sleeps long enough to outlive the join timeout."""

    def _sleep():
        time.sleep(30)

    t = threading.Thread(target=_sleep, daemon=True)
    t.start()
    return t


def _dead_thread() -> threading.Thread:
    t = threading.Thread(target=lambda: None, daemon=True)
    t.start()
    t.join()
    return t


def test_stop_unknown_session_does_not_crash() -> None:
    runner = NativeTradingNodeSessionRunner()
    result = runner.stop(session_id="never_existed")
    assert result.status == "NOT_FOUND"
    assert any(e["status"] == "NOT_FOUND" for e in result.lifecycle_events)


def test_double_stop_does_not_crash() -> None:
    runner = NativeTradingNodeSessionRunner()
    node = _FakeNode()
    runner._sessions["s1"] = (node, _dead_thread())

    first = runner.stop(session_id="s1")
    assert first.status in ("DISPOSED", "STOP_TIMEOUT")

    # Second stop for the now-removed session must be a clean NOT_FOUND, not KeyError.
    second = runner.stop(session_id="s1")
    assert second.status == "NOT_FOUND"


def test_normal_stop_calls_stop_join_dispose() -> None:
    runner = NativeTradingNodeSessionRunner()
    node = _FakeNode()
    runner._sessions["s2"] = (node, _dead_thread())

    result = runner.stop(session_id="s2")

    assert result.status == "DISPOSED"
    assert node.stopped is True
    assert node.disposed is True
    assert "s2" not in runner._sessions
    statuses = [e["status"] for e in result.lifecycle_events]
    assert "STOPPED" in statuses
    assert "DISPOSED" in statuses


def test_hung_node_records_stop_timeout_and_skips_dispose() -> None:
    runner = NativeTradingNodeSessionRunner()
    node = _FakeNode(hang=True)  # dispose() asserts it is NOT called
    runner._sessions["s3"] = (node, _hung_thread())

    try:
        result = runner.stop(session_id="s3")
    finally:
        # Clean up the hung thread so the test process can exit.
        pass

    assert result.status == "STOP_TIMEOUT"
    assert node.stopped is True
    statuses = [e["status"] for e in result.lifecycle_events]
    assert "STOP_TIMEOUT" in statuses
    # DISPOSED must NOT be claimed when the thread is still alive.
    assert "DISPOSED" not in statuses
