from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass

from .engine_contract import NAUTILUS_TRADER_VERSION


@dataclass(frozen=True)
class NautilusRuntimeVersionStatus:
    package_name: str
    expected_version: str
    installed_version: str | None
    is_match: bool
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
            message=f"expected {package_name}=={NAUTILUS_TRADER_VERSION}, but package is not installed",
        )

    is_match = installed_version == NAUTILUS_TRADER_VERSION
    if is_match:
        message = f"{package_name} runtime matches pinned version {NAUTILUS_TRADER_VERSION}"
    else:
        message = f"expected {package_name}=={NAUTILUS_TRADER_VERSION}, got {installed_version}"
    return NautilusRuntimeVersionStatus(
        package_name=package_name,
        expected_version=NAUTILUS_TRADER_VERSION,
        installed_version=installed_version,
        is_match=is_match,
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
