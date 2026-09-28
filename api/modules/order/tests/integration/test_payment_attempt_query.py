"""Integration tests for the payment-attempt modification queries (test DB)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from modules.order.infrastructure.adapters.driven.prisma.payment_attempt_query import (
    PrismaPaymentAttemptQuery,
)

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _clean(db):
    yield
    db.payment.delete_many(where={})
    db.order.delete_many(where={})


def _seed(db, *, version: int = 0, status: str = "APPROVED", superseded: bool = False):
    business_id = str(uuid4())
    order_id = str(uuid4())
    attempt_id = str(uuid4())
    db.businessconfiguration.create(
        {
            "id": business_id,
            "businessName": "Attempt Test Biz",
            "minOrder": Decimal("0"),
            "shippingCost": Decimal("0"),
        }
    )
    db.order.create(
        {
            "id": order_id,
            "status": "PENDING",
            "origin": "AGENT",
            "subtotal": Decimal("0"),
            "discount": Decimal("0"),
            "businessConfigId": business_id,
        }
    )
    db.payment.create(
        {
            "id": attempt_id,
            "orderId": order_id,
            "orderVersion": version,
            "provider": "MERCADOPAGO",
            "amount": Decimal("1000"),
            "status": status,
            "supersededAt": (
                datetime(2026, 9, 16, tzinfo=timezone.utc) if superseded else None
            ),
        }
    )
    return order_id, attempt_id


def test_has_current_approved_matches_the_version(db) -> None:
    order_id, _ = _seed(db, version=0, status="APPROVED")
    query = PrismaPaymentAttemptQuery(db)

    assert query.has_current_approved(order_id, 0) is True
    assert query.has_current_approved(order_id, 1) is False


def test_superseded_attempt_is_not_current(db) -> None:
    order_id, _ = _seed(db, version=0, status="APPROVED", superseded=True)
    query = PrismaPaymentAttemptQuery(db)

    assert query.has_current_approved(order_id, 0) is False
    assert query.current_for_version(order_id, 0) is None


def test_supersede_marks_the_live_attempt_and_returns_its_id(db) -> None:
    order_id, attempt_id = _seed(db, version=0, status="PENDING")
    query = PrismaPaymentAttemptQuery(db)
    at = datetime(2026, 9, 17, tzinfo=timezone.utc)

    superseded_ids = query.supersede_current(order_id, 0, at)

    assert superseded_ids == [attempt_id]
    assert query.has_current_approved(order_id, 0) is False
    assert query.current_for_version(order_id, 0) is None

    row = db.payment.find_unique(where={"id": attempt_id})
    assert row is not None
    assert row.supersededAt is not None
    assert row.cancellationStatus == "PENDING"


def test_current_for_version_returns_the_attempt_view(db) -> None:
    order_id, attempt_id = _seed(db, version=3, status="PENDING")
    query = PrismaPaymentAttemptQuery(db)

    view = query.current_for_version(order_id, 3)

    assert view is not None
    assert view.id == attempt_id
    assert view.order_version == 3
    assert view.superseded is False
    assert view.amount == Decimal("1000")
