from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import ExecutionLaneMode

_ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,80}$")
_ALLOWED_SUFFIXES = (
    "API_KEY",
    "API_SECRET",
    "API_PASSPHRASE",
    "PRIVATE_KEY",
    "WALLET_ADDRESS",
    "TESTNET",
    "BASE_URL",
    "ACCOUNT_ID",
    "SUBACCOUNT_ID",
)
_FORBIDDEN_PREFIXES = ("NEXT_PUBLIC_",)
_FORBIDDEN_KEYS = {
    "API_KEY",
    "API_SECRET",
    "SECRET",
    "SECRET_KEY",
    "PRIVATE_KEY",
    "PASSWORD",
    "TOKEN",
    "AUTHORIZATION",
    "BUILDER_API_TOKEN",
    "BUILDER_DEV_AUTH_TOKEN",
    "OPENAI_API_KEY",
}
_DEFAULT_ENV_FILE = ".env.execution.local"


class ExecutionCredentialSlotRequest(BaseModel):
    """One-shot local/dev credential bootstrap request.

    The request is intentionally separate from runtime profile and command
    payloads so StrategySpec/backtest/execution requests never carry raw
    credentials. The backend writes the values into a gitignored local env file
    and returns only a slot ref plus redacted metadata.
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    lane_mode: ExecutionLaneMode
    requested_by: str = Field(min_length=1)
    credential_values: dict[str, str] = Field(min_length=1)
    storage_target: str = _DEFAULT_ENV_FILE

    @field_validator("venue", "adapter_id")
    @classmethod
    def normalize_upper(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("storage_target")
    @classmethod
    def validate_storage_target(cls, value: str) -> str:
        target = value.strip() or _DEFAULT_ENV_FILE
        path = Path(target)
        if target != _DEFAULT_ENV_FILE or path.name != target or "/" in target or "\\" in target:
            raise ValueError("credential storage target must be .env.execution.local")
        return target

    @model_validator(mode="after")
    def validate_credential_values(self) -> "ExecutionCredentialSlotRequest":
        normalized: dict[str, str] = {}
        venue_prefix = f"{self.venue.strip().upper()}_"
        for raw_key, raw_value in self.credential_values.items():
            key = str(raw_key).strip().upper()
            value = str(raw_value)
            _validate_env_key(key, venue_prefix=venue_prefix)
            _validate_env_value(value, key=key)
            normalized[key] = value
        self.credential_values = dict(sorted(normalized.items()))
        return self


class ExecutionCredentialSlot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    credential_slot_ref: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    runtime_profile_id: str = Field(min_length=1)
    adapter_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    lane_mode: ExecutionLaneMode
    requested_by: str = Field(min_length=1)
    secrets_storage: Literal["local_env_file"] = "local_env_file"
    env_file_path: str = _DEFAULT_ENV_FILE
    redacted_keys: list[str]
    fingerprint: str = Field(min_length=64, max_length=64)
    browser_secret_echo: Literal[False] = False


class LocalEnvCredentialSlotStore:
    """Persist execution-lane credentials to a local env file without echoing secrets."""

    def __init__(self, *, base_dir: str | Path | None = None, env_file_name: str = _DEFAULT_ENV_FILE) -> None:
        self._base_dir = Path(base_dir or os.getcwd()).resolve()
        self._env_file_name = env_file_name
        if Path(env_file_name).name != env_file_name:
            raise ValueError("credential env file name must not contain path separators")

    @property
    def env_file_path(self) -> Path:
        return self._base_dir / self._env_file_name

    def create_slot(self, request: ExecutionCredentialSlotRequest) -> ExecutionCredentialSlot:
        env_file = self._write_env_values(request.credential_values)
        fingerprint = _fingerprint(request.credential_values)
        slot_ref = _slot_ref(request=request, fingerprint=fingerprint)
        return ExecutionCredentialSlot(
            credential_slot_ref=slot_ref,
            tenant_id=request.tenant_id,
            project_id=request.project_id,
            runtime_profile_id=request.runtime_profile_id,
            adapter_id=request.adapter_id,
            venue=request.venue,
            lane_mode=request.lane_mode,
            requested_by=request.requested_by,
            env_file_path=env_file.name,
            redacted_keys=sorted(request.credential_values),
            fingerprint=fingerprint,
            browser_secret_echo=False,
        )

    def _write_env_values(self, values: dict[str, str]) -> Path:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        env_file = self.env_file_path
        existing = _read_env_file(env_file)
        existing.update(values)
        body = "\n".join(f"{key}={value}" for key, value in sorted(existing.items())) + "\n"
        env_file.write_text(body, encoding="utf-8")
        try:
            env_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except PermissionError:
            # Some filesystems in CI/containers may not allow chmod. The content
            # is still written to a gitignored local file; callers can harden perms.
            pass
        return env_file

    def resolve_slot_values(self, slot: ExecutionCredentialSlot) -> dict[str, str]:
        """Read the local env-file values for a previously created slot.

        Callers must not include the returned raw values in reports or API
        responses. They are for backend-owned adapter config construction only.
        """

        values = _read_env_file(self.env_file_path)
        resolved = {key: values[key] for key in slot.redacted_keys if key in values}
        missing = sorted(set(slot.redacted_keys) - set(resolved))
        if missing:
            raise ValueError(f"credential slot env values missing: {', '.join(missing)}")
        return resolved


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()
        if key:
            values[key] = value
    return values


def _validate_env_key(key: str, *, venue_prefix: str) -> None:
    if not _ENV_KEY_RE.match(key) or any(key.startswith(prefix) for prefix in _FORBIDDEN_PREFIXES):
        raise ValueError(f"unsafe credential env key: {key}")
    if key in _FORBIDDEN_KEYS:
        raise ValueError(f"credential env key must be venue-prefixed: {key}")
    if not key.startswith(venue_prefix):
        raise ValueError(f"credential env key must be venue-prefixed: {key}")
    if not any(key.endswith(suffix) for suffix in _ALLOWED_SUFFIXES):
        raise ValueError(f"unsafe credential env key: {key}")


def _validate_env_value(value: str, *, key: str) -> None:
    if value.strip() == "":
        raise ValueError(f"credential value for {key} is required")
    if "\n" in value or "\r" in value or "\x00" in value:
        raise ValueError(f"credential value for {key} contains unsafe characters")


def _fingerprint(values: dict[str, str]) -> str:
    material = {
        key: hashlib.sha256(value.encode("utf-8")).hexdigest()
        for key, value in sorted(values.items())
    }
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _slot_ref(*, request: ExecutionCredentialSlotRequest, fingerprint: str) -> str:
    return (
        "credslot://local-env/"
        f"{_safe_ref_part(request.project_id)}/"
        f"{_safe_ref_part(request.runtime_profile_id)}/"
        f"{_safe_ref_part(request.venue.lower())}/"
        f"{fingerprint[:12]}"
    )


def _safe_ref_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-_") or "unknown"
