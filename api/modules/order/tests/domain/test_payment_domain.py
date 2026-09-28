from datetime import datetime, timezone
from decimal import Decimal

from modules.order.domain.models.cancellation_status import CancellationStatus
from modules.order.domain.models.payment_attempt import PaymentAttempt
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
    payment = PaymentAttempt(
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
    payment = PaymentAttempt(
        id="pay-2",
        order_id="order-1",
        provider="MERCADOPAGO",
        amount=Decimal("2500.00"),
        status=PaymentStatus.PENDING,
    )

    assert not payment.has_same_final_status(PaymentStatus.PENDING)
    assert not payment.has_same_final_status(PaymentStatus.APPROVED)


def _attempt(**overrides):
    base = dict(
        id="att-1",
        order_id="o-1",
        provider="MERCADOPAGO",
        amount=Decimal("1000"),
        status=PaymentStatus.PENDING,
        order_version=5,
    )
    base.update(overrides)
    return PaymentAttempt(**base)


def test_provider_status_and_supersede_are_independent():
    attempt = _attempt(status=PaymentStatus.APPROVED)
    attempt.supersede(datetime(2026, 9, 17, tzinfo=timezone.utc))

    # A stale checkout can have been paid AND be obsolete locally.
    assert attempt.is_approved() is True
    assert attempt.superseded is True
    assert attempt.cancellation_status is CancellationStatus.PENDING


def test_is_current_for_matches_version_and_supersede():
    assert _attempt(order_version=5).is_current_for(5) is True
    assert _attempt(order_version=5).is_current_for(6) is False

    superseded = _attempt(order_version=5)
    superseded.supersede(datetime(2026, 9, 17, tzinfo=timezone.utc))
    assert superseded.is_current_for(5) is False


def test_supersede_keeps_the_first_timestamp():
    attempt = _attempt()
    first = datetime(2026, 9, 17, tzinfo=timezone.utc)
    attempt.supersede(first)
    attempt.supersede(datetime(2026, 9, 18, tzinfo=timezone.utc))

    assert attempt.superseded_at == first


def test_checkout_creation_stores_provider_identity():
    attempt = _attempt()
    attempt.mark_checkout_created(
        external_id="MP-1", checkout_url="https://mp/checkout", external_reference="o-1"
    )

    assert attempt.external_id == "MP-1"
    assert attempt.checkout_url == "https://mp/checkout"
    assert attempt.external_reference == "o-1"


def test_cancellation_lifecycle():
    attempt = _attempt()

    attempt.mark_remote_cancelled()
    assert attempt.cancellation_status is CancellationStatus.CANCELLED
    assert attempt.cancellation_status.is_open() is False

    attempt.mark_remote_already_cancelled()
    assert attempt.cancellation_status is CancellationStatus.REMOTE_ALREADY_CANCELLED

    attempt.mark_cancellation_failed()
    assert attempt.cancellation_status is CancellationStatus.FAILED
    assert attempt.cancellation_status.is_open() is True

    assert CancellationStatus.PENDING.is_open() is True
