"""Adapter auto-discovery factory pattern.

Provides a decorator-based registration system where new adapter modules
can register themselves via @register_adapter. The discovery system
maintains a registry of AdapterFactory instances that can produce
AdapterProfile objects on demand.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from packages.adapter_registry.models import AdapterProfile


class AdapterFactory(ABC):
    """Base class for adapter factories.

    Subclass this and implement profile_id and build_profile(),
    then register with @register_adapter.
    """

    @property
    @abstractmethod
    def profile_id(self) -> str:
        """Unique identifier for this adapter factory."""

    @abstractmethod
    def build_profile(self) -> AdapterProfile:
        """Build and return the AdapterProfile for this adapter."""


# Global registry of factory classes
_FACTORY_REGISTRY: dict[str, type[AdapterFactory]] = {}


def register_adapter(cls: type[AdapterFactory]) -> type[AdapterFactory]:
    """Decorator to register an AdapterFactory subclass.

    Usage:
        @register_adapter
        class MyAdapterFactory(AdapterFactory):
            ...
    """
    # Instantiate to get the profile_id without full build
    instance = cls()
    pid = instance.profile_id
    _FACTORY_REGISTRY[pid] = cls
    return cls


def discover_adapter(adapter_id: str) -> AdapterProfile | None:
    """Look up a registered adapter and return its profile, or None."""
    factory_cls = _FACTORY_REGISTRY.get(adapter_id)
    if factory_cls is None:
        return None
    return factory_cls().build_profile()


def adapter_factory(adapter_id: str) -> AdapterProfile | None:
    """Build and return an AdapterProfile from a registered factory.

    Alias for discover_adapter for convenience.
    """
    return discover_adapter(adapter_id)


def list_discovered_adapters() -> list[str]:
    """Return list of all registered adapter IDs."""
    return sorted(_FACTORY_REGISTRY.keys())
