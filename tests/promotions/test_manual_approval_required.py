from __future__ import annotations

import pytest

from packages.promotions.service import PromotionService


def test_final_promotion_requires_manual_approval() -> None:
    service = PromotionService()

    with pytest.raises(ValueError, match="manual approval"):
        service.create_final_candidate(
            strategy_version="0.3.0-beta.1",
            compile_hash="abc123",
            gate_compatibility=True,
            manual_approval=False,
        )
