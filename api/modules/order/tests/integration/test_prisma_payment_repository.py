from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus
from modules.order.infrastructure.adapters.driven.prisma.payment_repository import (
    PrismaPaymentRepository,
)

pytestmark = pytest.mark.db
pytest_plugins = ["shared.infrastructure.prisma.tests.conftest"]


@pytest.fixture(autouse=True)
def _clean_payments(db):
    yield
    db.payment.delete_many(where={})
    db.order.delete_many(where={})


def _create_order(db) -> str:
    order_id = str(uuid4())
    db.order.create(
        {
            "id": order_id,
            "status": "PENDING",
            "origin": "AGENT",
            "subtotal": Decimal("1500.00"),
            "discount": Decimal("0.00"),
            "paymentType": "ONLINE",
            "totalAmount": Decimal("1500.00"),
        }
    )
    return order_id


def test_create_pending_payment_and_lookup_by_external_reference(db) -> None:
    order_id = _create_order(db)
    repo = PrismaPaymentRepository(db)

    payment = repo.create_pending(
        order_id=order_id,
        provider="MERCADOPAGO",
        amount=Decimal("1500.00"),
        external_reference=order_id,
    )

    assert payment.order_id == order_id
    assert payment.provider == "MERCADOPAGO"
    assert payment.amount == Decimal("1500.00")
    assert payment.status == PaymentStatus.PENDING
    assert payment.external_reference == order_id

    found = repo.get_by_external_reference(order_id)

    assert found is not None
    assert found.id == payment.id
    assert found.external_reference == order_id


def test_save_provider_data_and_lookup_by_external_and_preference_ids(db) -> None:
    order_id = _create_order(db)
    repo = PrismaPaymentRepository(db)
    payment = repo.create_pending(
        order_id=order_id,
        provider="MERCADOPAGO",
        amount=Decimal("1500.00"),
        external_reference=order_id,
    )
    payment.external_id = "mp-payment-123"
    payment.preference_id = "mp-pref-123"
    payment.checkout_url = "https://mercadopago.example/checkout"
    payment.expires_at = datetime(2026, 9, 9, tzinfo=timezone.utc)

    saved = repo.save(payment)

    assert saved.external_id == "mp-payment-123"
    assert saved.preference_id == "mp-pref-123"
    assert saved.checkout_url == "https://mercadopago.example/checkout"
    assert saved.expires_at is not None

    by_external_id = repo.get_by_external_id("mp-payment-123")
    by_preference_id = repo.get_by_preference_id("mp-pref-123")

    assert by_external_id is not None
    assert by_external_id.id == payment.id
    assert by_preference_id is not None
    assert by_preference_id.id == payment.id


def test_update_status_persists_payment_status(db) -> None:
    order_id = _create_order(db)
    repo = PrismaPaymentRepository(db)
    payment = repo.create_pending(
        order_id=order_id,
        provider="MERCADOPAGO",
        amount=Decimal("1500.00"),
        external_reference=order_id,
    )

    updated = repo.update_status(payment.id, PaymentStatus.APPROVED)

    assert updated.status == PaymentStatus.APPROVED
    found = repo.get_by_external_reference(order_id)
    assert found is not None
    assert found.status == PaymentStatus.APPROVED


def test_save_updates_existing_payment_without_creating_duplicates(db) -> None:
    order_id = _create_order(db)
    repo = PrismaPaymentRepository(db)
    payment = repo.create_pending(
        order_id=order_id,
        provider="MERCADOPAGO",
        amount=Decimal("1500.00"),
        external_reference=order_id,
    )

    repo.save(
        Payment(
            id=payment.id,
            order_id=order_id,
            provider="MERCADOPAGO",
            amount=Decimal("1500.00"),
            status=PaymentStatus.REJECTED,
            external_id="mp-payment-456",
            preference_id="mp-pref-456",
            checkout_url="https://mercadopago.example/retry",
            external_reference=order_id,
        )
    )

    rows = db.payment.find_many(where={"orderId": order_id})

    assert len(rows) == 1
    assert rows[0].status == "REJECTED"
    assert rows[0].externalId == "mp-payment-456"
