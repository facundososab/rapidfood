"""Per-business WhatsApp configuration repository (Prisma, integration).

Proves the mapping, the unique-per-business upsert, the phone lookup, and that
the access token / app secret are stored ENCRYPTED at rest.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)
from modules.conversation.infrastructure.adapters.driven.prisma.whatsapp_configuration_repository import (
    PrismaWhatsAppConfigurationRepository,
)

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _clean(db):
    yield
    db.whatsappconfiguration.delete_many(where={})
    db.businessconfiguration.delete_many(where={})


def _seed(db) -> str:
    business_id = str(uuid4())
    db.businessconfiguration.create(
        {
            "id": business_id,
            "businessName": "WhatsApp Test Biz",
            "minOrder": Decimal("0"),
            "shippingCost": Decimal("0"),
        }
    )
    return business_id


def test_upsert_roundtrips_and_encrypts_secrets(db):
    business_id = _seed(db)
    repo = PrismaWhatsAppConfigurationRepository(db)

    assert repo.get_by_business_config_id(business_id) is None

    saved = repo.upsert(
        WhatsAppConfiguration(
            business_config_id=business_id,
            phone_number_id="111111",
            verify_token="verify-me",
            access_token="ACCESS-TOKEN",
            app_secret="APP-SECRET",
        )
    )
    fetched = repo.get_by_business_config_id(business_id)
    assert fetched.access_token == "ACCESS-TOKEN"
    assert fetched.app_secret == "APP-SECRET"
    assert fetched.verify_token == "verify-me"

    # The raw column must NOT contain the plaintext secret.
    row = db.whatsappconfiguration.find_unique(
        where={"businessConfigId": business_id}
    )
    assert row.accessTokenEnc != "ACCESS-TOKEN"
    assert row.appSecretEnc != "APP-SECRET"

    # Lookup by phone_number_id and active list.
    assert repo.get_by_phone_number_id("111111").business_config_id == business_id
    assert [c.business_config_id for c in repo.list_active()] == [business_id]

    # A second upsert updates the same row (one config per business).
    repo.upsert(
        WhatsAppConfiguration(
            id=saved.id,
            business_config_id=business_id,
            phone_number_id="222222",
            verify_token="verify-2",
            access_token="ACCESS-TOKEN-2",
            app_secret="APP-SECRET-2",
        )
    )
    assert repo.get_by_phone_number_id("111111") is None
    updated = repo.get_by_phone_number_id("222222")
    assert updated.access_token == "ACCESS-TOKEN-2"
