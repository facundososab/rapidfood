"""One active order (DRAFT/PENDING) per conversation, enforced by a partial index.

Regression for the duplicated-active-order bug: a parallel create must not leave
two active orders for the same conversation (the leftover DRAFT used to shadow
the confirmed PENDING order and break create_payment_checkout).
"""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from modules.order.domain.errors.order_errors import DuplicateActiveOrderError
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_origin import OrderOrigin
from modules.order.domain.models.order_state import OrderState
from modules.order.infrastructure.adapters.driven.prisma.order_repository import (
    PrismaOrderRepository,
)

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _clean(db):
    yield
    db.order.delete_many(where={})
    db.conversation.delete_many(where={})
    db.businessconfiguration.delete_many(where={})


def _seed(db) -> tuple[str, str]:
    business_id = str(uuid4())
    conversation_id = str(uuid4())
    db.businessconfiguration.create(
        {
            "id": business_id,
            "businessName": "One Active Order Biz",
            "minOrder": Decimal("0"),
            "shippingCost": Decimal("0"),
        }
    )
    db.conversation.create(
        {
            "id": conversation_id,
            "businessConfigId": business_id,
            "channel": "LANGSMITH",
            "externalThreadId": str(uuid4()),
        }
    )
    return business_id, conversation_id


def _order(conversation_id: str, business_id: str, status=OrderState.DRAFT) -> Order:
    return Order(
        id=str(uuid4()),
        status=status,
        subtotal=Decimal("0"),
        discount=Decimal("0"),
        business_config_id=business_id,
        conversation_id=conversation_id,
        origin=OrderOrigin.AGENT,
    )


def test_a_second_active_order_for_a_conversation_is_rejected(db):
    business_id, conversation_id = _seed(db)
    repo = PrismaOrderRepository()

    repo.save(_order(conversation_id, business_id))

    with pytest.raises(DuplicateActiveOrderError):
        repo.save(_order(conversation_id, business_id, status=OrderState.PENDING))


def test_a_finished_order_frees_the_conversation_for_a_new_active_order(db):
    business_id, conversation_id = _seed(db)
    repo = PrismaOrderRepository()

    first = _order(conversation_id, business_id)
    repo.save(first)
    first.status = OrderState.CANCELLED
    repo.save(first)

    # Must NOT raise: cancelled orders are not "active".
    repo.save(_order(conversation_id, business_id))


def test_orders_without_a_conversation_are_not_constrained(db):
    business_id, _ = _seed(db)
    repo = PrismaOrderRepository()

    repo.save(_order(None, business_id))
    repo.save(_order(None, business_id))
