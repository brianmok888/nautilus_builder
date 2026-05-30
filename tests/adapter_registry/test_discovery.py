"""Tests for adapter auto-discovery factory pattern (S16)."""
import pytest
from packages.adapter_registry.discovery import (
    AdapterFactory,
    adapter_factory,
    discover_adapter,
    list_discovered_adapters,
    register_adapter,
)
from packages.adapter_registry.models import AdapterProfile


class TestAdapterFactory:
    """Verify AdapterFactory base class."""

    def test_adapter_factory_is_abstract(self):
        """AdapterFactory should define the expected interface."""
        assert hasattr(AdapterFactory, "profile_id")
        assert hasattr(AdapterFactory, "build_profile")

    def test_adapter_factory_subclass(self):
        """Should be able to create a concrete factory."""
        class MyFactory(AdapterFactory):
            @property
            def profile_id(self) -> str:
                return "TEST_VENUE"

            def build_profile(self) -> AdapterProfile:
                return AdapterProfile(
                    adapter_id="TEST_VENUE",
                    enabled=True,
                    venue="TEST",
                    asset_class="crypto_perp",
                    data_modes=["historical_bars"],
                    execution_modes={"backtest": True, "paper": False, "live": False},
                )

        factory = MyFactory()
        assert factory.profile_id == "TEST_VENUE"
        profile = factory.build_profile()
        assert profile.adapter_id == "TEST_VENUE"
        assert profile.enabled


class TestAdapterRegistration:
    """Verify decorator-based adapter registration."""

    def test_register_adapter_decorator(self):
        """register_adapter should register a factory class."""
        @register_adapter
        class DemoFactory(AdapterFactory):
            @property
            def profile_id(self) -> str:
                return "DEMO_ADAPTER"

            def build_profile(self) -> AdapterProfile:
                return AdapterProfile(
                    adapter_id="DEMO_ADAPTER",
                    enabled=True,
                    venue="DEMO",
                    asset_class="crypto_perp",
                    data_modes=["historical_bars"],
                    execution_modes={"backtest": True, "paper": False, "live": False},
                )

        assert "DEMO_ADAPTER" in list_discovered_adapters()

    def test_discover_registered_adapter(self):
        """discover_adapter should return a profile for registered adapters."""
        @register_adapter
        class FindableFactory(AdapterFactory):
            @property
            def profile_id(self) -> str:
                return "FINDABLE"

            def build_profile(self) -> AdapterProfile:
                return AdapterProfile(
                    adapter_id="FINDABLE",
                    enabled=True,
                    venue="FIND",
                    asset_class="crypto_spot",
                    data_modes=["historical_bars"],
                    execution_modes={"backtest": True, "paper": False, "live": False},
                )

        profile = discover_adapter("FINDABLE")
        assert profile is not None
        assert profile.adapter_id == "FINDABLE"

    def test_discover_unknown_adapter_returns_none(self):
        """discover_adapter should return None for unknown adapters."""
        result = discover_adapter("NONEXISTENT_ADAPTER_XYZ")
        assert result is None

    def test_list_discovered_adapters_returns_list(self):
        """list_discovered_adapters should return a list of adapter IDs."""
        adapters = list_discovered_adapters()
        assert isinstance(adapters, list)
        assert len(adapters) >= 0


class TestAdapterFactoryFunction:
    """Verify adapter_factory helper."""

    def test_adapter_factory_builds_profile(self):
        """adapter_factory should build a profile from a factory."""
        @register_adapter
        class BuildableFactory(AdapterFactory):
            @property
            def profile_id(self) -> str:
                return "BUILDABLE"

            def build_profile(self) -> AdapterProfile:
                return AdapterProfile(
                    adapter_id="BUILDABLE",
                    enabled=True,
                    venue="BLD",
                    asset_class="equity",
                    data_modes=["historical_bars", "trade_ticks"],
                    execution_modes={"backtest": True, "paper": False, "live": False},
                )

        profile = adapter_factory("BUILDABLE")
        assert profile is not None
        assert profile.asset_class == "equity"

    def test_adapter_factory_returns_none_for_unknown(self):
        """adapter_factory should return None for unregistered adapters."""
        result = adapter_factory("UNKNOWN_FACTORY")
        assert result is None
