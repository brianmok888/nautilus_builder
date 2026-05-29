from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass

from .engine_contract import NAUTILUS_TRADER_VERSION


_PINNED_MAJOR, _PINNED_MINOR, _PINNED_PATCH = (int(x) for x in NAUTILUS_TRADER_VERSION.split("."))


@dataclass(frozen=True)
class NautilusRuntimeVersionStatus:
    package_name: str
    expected_version: str
    installed_version: str | None
    is_match: bool
    is_minor_drift: bool
    message: str


def check_nautilus_runtime_version(*, package_name: str = "nautilus_trader") -> NautilusRuntimeVersionStatus:
    try:
        installed_version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return NautilusRuntimeVersionStatus(
            package_name=package_name,
            expected_version=NAUTILUS_TRADER_VERSION,
            installed_version=None,
            is_match=False,
            is_minor_drift=False,
            message=f"expected {package_name}=={NAUTILUS_TRADER_VERSION}, but package is not installed",
        )

    is_match = installed_version == NAUTILUS_TRADER_VERSION
    is_minor_drift = False

    if is_match:
        message = f"{package_name} runtime matches pinned version {NAUTILUS_TRADER_VERSION}"
    else:
        try:
            parts = installed_version.split(".")
            inst_major, inst_minor = int(parts[0]), int(parts[1])
            if inst_major != _PINNED_MAJOR or inst_minor != _PINNED_MINOR:
                is_minor_drift = True
                message = f"VERSION DRIFT: expected {package_name}=={NAUTILUS_TRADER_VERSION}, got {installed_version}. Migration required."
            else:
                message = f"PATCH DRIFT: expected {package_name}=={NAUTILUS_TRADER_VERSION}, got {installed_version}. Patch-only difference."
        except (ValueError, IndexError):
            message = f"expected {package_name}=={NAUTILUS_TRADER_VERSION}, got {installed_version}"

    return NautilusRuntimeVersionStatus(
        package_name=package_name,
        expected_version=NAUTILUS_TRADER_VERSION,
        installed_version=installed_version,
        is_match=is_match,
        is_minor_drift=is_minor_drift,
        message=message,
    )


def assert_nautilus_runtime_version() -> NautilusRuntimeVersionStatus:
    status = check_nautilus_runtime_version()
    if not status.is_match:
        raise RuntimeError(status.message)
    return status


if __name__ == "__main__":
    current = assert_nautilus_runtime_version()
    print(current.message)
