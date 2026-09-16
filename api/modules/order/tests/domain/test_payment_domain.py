from decimal import Decimal

from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus


def test_payment_status_values_match_payment_lifecycle():
    assert [status.value for status in PaymentStatus] == [
        "PENDING",
        "APPROVED",
        "REJECTED",
        "FAILED",
        "EXPIRED",
    ]


def test_payment_final_statuses_are_terminal_for_idempotency():
    assert PaymentStatus.APPROVED.is_final()
    assert PaymentStatus.REJECTED.is_final()
    assert PaymentStatus.FAILED.is_final()
    assert PaymentStatus.EXPIRED.is_final()
    assert not PaymentStatus.PENDING.is_final()


def test_payment_detects_duplicate_final_status():
    payment = Payment(
        id="pay-1",
        order_id="order-1",
        provider="MERCADOPAGO",
        amount=Decimal("1500.00"),
        status=PaymentStatus.APPROVED,
    )

    assert payment.has_same_final_status(PaymentStatus.APPROVED)
    assert not payment.has_same_final_status(PaymentStatus.REJECTED)
    assert not payment.has_same_final_status(PaymentStatus.PENDING)


def test_pending_payment_is_not_duplicate_final_status():
    payment = Payment(
        id="pay-2",
        order_id="order-1",
        provider="MERCADOPAGO",
        amount=Decimal("2500.00"),
        status=PaymentStatus.PENDING,
    )

    assert not payment.has_same_final_status(PaymentStatus.PENDING)
    assert not payment.has_same_final_status(PaymentStatus.APPROVED)
