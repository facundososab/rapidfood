"""Preparation-time configuration repository (Prisma, integration)."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from modules.order.domain.models.preparation_time_config import PreparationTimeConfig
from modules.order.infrastructure.adapters.driven.prisma.preparation_time_config_repository import (
    PrismaPreparationTimeConfigRepository,
)

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _clean(db):
    yield
    db.preparationtimeconfiguration.delete_many(where={})
    db.businessconfiguration.delete_many(where={})


def _seed(db) -> str:
    business_id = str(uuid4())
    db.businessconfiguration.create(
        {
            "id": business_id,
            "businessName": "Prep Time Test Biz",
            "minOrder": Decimal("0"),
            "shippingCost": Decimal("0"),
        }
    )
    return business_id


def test_get_returns_none_when_unset_and_roundtrips_an_upsert(db):
    business_id = _seed(db)
    repo = PrismaPreparationTimeConfigRepository(db)

    assert repo.get(business_id) is None

    config = PreparationTimeConfig(
        high_demand_threshold=8,
        very_high_demand_threshold=15,
        normal_prep_minutes=20,
        high_demand_prep_minutes=35,
        very_high_demand_prep_minutes=50,
        buffer_minutes=5,
    )
    repo.save(business_id, config)
    assert repo.get(business_id) == config

    # Upsert updates the same row (one config per business).
    updated = PreparationTimeConfig(
        high_demand_threshold=10,
        very_high_demand_threshold=20,
        normal_prep_minutes=15,
        high_demand_prep_minutes=30,
        very_high_demand_prep_minutes=45,
        buffer_minutes=7,
    )
    repo.save(business_id, updated)
    assert repo.get(business_id) == updated
