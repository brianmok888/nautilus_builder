"""TDD tests for ExecutionLaneService bounded stores (C-01).

Tests the max_reports and max_sessions capacity parameters and LRU eviction
behavior without requiring full command/profile validation.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from packages.execution_lane.service import ExecutionLaneService


class TestServiceInit:
    def test_default_init_no_args(self):
        service = ExecutionLaneService()
        assert len(service._profiles) == 0
        assert service._max_reports is None
        assert service._max_sessions is None

    def test_init_with_bounds(self):
        service = ExecutionLaneService(max_reports=50, max_sessions=10)
        assert service._max_reports == 50
        assert service._max_sessions == 10


class TestReportEviction:
    def test_evict_reports_removes_oldest_when_over_capacity(self):
        service = ExecutionLaneService(max_reports=3)
        # Directly insert mock reports
        for i in range(5):
            service._reports[f"report-{i}"] = MagicMock(report_id=f"report-{i}")
        service._evict_reports_if_needed()
        assert len(service._reports) == 3
        # Oldest should be evicted (report-0, report-1)
        assert "report-0" not in service._reports
        assert "report-1" not in service._reports
        assert "report-2" in service._reports
        assert "report-3" in service._reports
        assert "report-4" in service._reports

    def test_no_eviction_when_under_capacity(self):
        service = ExecutionLaneService(max_reports=10)
        service._reports["r1"] = MagicMock()
        service._evict_reports_if_needed()
        assert len(service._reports) == 1

    def test_no_eviction_when_max_reports_is_none(self):
        service = ExecutionLaneService()
        for i in range(100):
            service._reports[f"r-{i}"] = MagicMock()
        service._evict_reports_if_needed()
        assert len(service._reports) == 100


class TestSessionEviction:
    def test_evict_sessions_removes_oldest_when_over_capacity(self):
        service = ExecutionLaneService(max_sessions=2)
        for i in range(4):
            service._sessions[f"session-{i}"] = MagicMock(session_id=f"session-{i}")
        service._evict_sessions_if_needed()
        assert len(service._sessions) == 2
        assert "session-0" not in service._sessions
        assert "session-1" not in service._sessions
        assert "session-2" in service._sessions
        assert "session-3" in service._sessions

    def test_no_eviction_when_max_sessions_is_none(self):
        service = ExecutionLaneService()
        for i in range(50):
            service._sessions[f"s-{i}"] = MagicMock()
        service._evict_sessions_if_needed()
        assert len(service._sessions) == 50
