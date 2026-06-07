#!/usr/bin/env python3
"""Demo: Adapter registry — lookup, list, and profile inspection.

Shows how to interact with the adapter registry to discover available
adapters, look up profiles, and understand what adapters are registered.
Run from repo root: python3 docs/examples/demo_adapter_discovery.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from packages.adapter_registry.service import AdapterRegistryService


def main() -> None:
    print("=" * 60)
    print("Demo: Adapter Registry Discovery")
    print("=" * 60)

    registry = AdapterRegistryService()

    # ── 1. List all enabled adapters ────────────────────────────
    profiles = registry.list_enabled_adapters()
    print(f"\n1. Enabled adapters ({len(profiles)}):")
    for profile in profiles:
        print(f"   - {profile.adapter_id} ({profile.venue})")
        print(f"     Asset class: {profile.asset_class}")
        print(f"     Data modes: {profile.data_modes}")
        print(f"     Execution: {profile.execution_modes}")

    # ── 2. Look up a specific adapter ───────────────────────────
    print("\n2. Looking up 'BINANCE_PERP' adapter:")
    try:
        binance = registry.get_adapter_profile("BINANCE_PERP")
        print(f"   Found: {binance.adapter_id}")
        print(f"   Venue: {binance.venue}")
        print(f"   Asset class: {binance.asset_class}")
        print(f"   Data modes: {binance.data_modes}")
    except ValueError as e:
        print(f"   Not found: {e}")

    # ── 3. Try a non-existent adapter ───────────────────────────
    print("\n3. Looking up non-existent adapter:")
    try:
        registry.get_adapter_profile("nonexistent_exchange")
        print("   ERROR: should have raised ValueError")
    except ValueError as e:
        print(f"   Correctly rejected: {e}")

    # ── 4. Try a disabled adapter ───────────────────────────────
    print("\n4. Looking up disabled adapter 'KRAKEN_SPOT':")
    try:
        registry.get_adapter_profile("KRAKEN_SPOT")
        print("   ERROR: should have raised ValueError")
    except ValueError as e:
        print(f"   Correctly rejected: {e}")

    # ── 5. Summary ──────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("Adapter registry summary:")
    print(f"  Enabled adapters: {len(profiles)}")
    print(f"  Adapter IDs: {[p.adapter_id for p in profiles]}")
    print("=" * 60)
    print("Demo complete.")


if __name__ == "__main__":
    main()
