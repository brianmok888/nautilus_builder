from __future__ import annotations

import os
from pathlib import Path

from .models import ExecutionLaneCommand, ExecutionLaneProfile, ExecutionLaneReport

_DEFAULT_PERSIST_DIR = ".omx/execution_lane"


class ExecutionLaneFilePersistence:
    """Serialize critical execution lane state to disk for recovery across restarts.

    Stores profiles, commands, and reports as JSON files under a configurable
    directory. This is a recovery seam, not a production database replacement.
    """

    def __init__(self, *, base_dir: str | Path | None = None) -> None:
        self._base_dir = Path(base_dir or os.getenv("BUILDER_EXECUTION_LANE_PERSIST_DIR", _DEFAULT_PERSIST_DIR))

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def _ensure_dir(self) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save_profile(self, profile: ExecutionLaneProfile) -> None:
        self._ensure_dir()
        path = self._base_dir / f"profile_{profile.runtime_profile_id}.json"
        path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

    def load_profile(self, runtime_profile_id: str) -> ExecutionLaneProfile | None:
        path = self._base_dir / f"profile_{runtime_profile_id}.json"
        if not path.exists():
            return None
        return ExecutionLaneProfile.model_validate_json(path.read_text(encoding="utf-8"))

    def save_command(self, command: ExecutionLaneCommand) -> None:
        self._ensure_dir()
        path = self._base_dir / f"command_{command.command_id}.json"
        path.write_text(command.model_dump_json(indent=2), encoding="utf-8")

    def load_command(self, command_id: str) -> ExecutionLaneCommand | None:
        path = self._base_dir / f"command_{command_id}.json"
        if not path.exists():
            return None
        return ExecutionLaneCommand.model_validate_json(path.read_text(encoding="utf-8"))

    def save_report(self, report: ExecutionLaneReport) -> None:
        self._ensure_dir()
        if not report.report_id:
            return
        path = self._base_dir / f"report_{report.report_id}.json"
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    def list_profile_ids(self) -> list[str]:
        if not self._base_dir.exists():
            return []
        return sorted(
            p.stem.replace("profile_", "")
            for p in self._base_dir.glob("profile_*.json")
        )

    def list_command_ids(self) -> list[str]:
        if not self._base_dir.exists():
            return []
        return sorted(
            p.stem.replace("command_", "")
            for p in self._base_dir.glob("command_*.json")
        )

    def list_report_ids(self) -> list[str]:
        if not self._base_dir.exists():
            return []
        return sorted(
            p.stem.replace("report_", "")
            for p in self._base_dir.glob("report_*.json")
        )
