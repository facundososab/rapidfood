"""Modification readiness and reopen rules."""
from datetime import datetime, timezone

import pytest

from modules.order.application.order_modification import (
    modification_readiness,
    prepare_order_for_modification,
)
from modules.order.domain.errors.order_errors import NewOrderRequiredError
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.tests.use_cases.fakes import FakeAttempts, make_order

NOW = datetime(2026, 9, 17, tzinfo=timezone.utc)


def test_draft_is_editable_without_reopen():
    readiness = modification_readiness(make_order(), FakeAttempts())
    assert readiness.editable is True
    assert readiness.requires_reopen is False
    assert readiness.requires_new_order is False


def test_pending_online_without_approved_is_reopenable():
    order = make_order(OrderState.PENDING, PaymentMethod.ONLINE)
    readiness = modification_readiness(order, FakeAttempts(has_approved=False))
    assert readiness.editable is True
    assert readiness.requires_reopen is True
    assert readiness.requires_new_order is False


def test_pending_without_payment_method_is_reopenable():
    """An unpaid PENDING order with no method is not "closed": it reopens.

    This is the state a premature confirmation used to leave behind, which
    forced a brand-new order just to choose how to pay.
    """
    order = make_order(OrderState.PENDING, None)
    readiness = modification_readiness(order, FakeAttempts())
    assert readiness.editable is True
    assert readiness.requires_reopen is True
    assert readiness.requires_new_order is False


def test_pending_online_with_approved_requires_new_order():
    order = make_order(OrderState.PENDING, PaymentMethod.ONLINE)
    readiness = modification_readiness(order, FakeAttempts(has_approved=True))
    assert readiness.editable is False
    assert readiness.requires_new_order is True


def test_pending_cash_requires_new_order():
    order = make_order(OrderState.PENDING, PaymentMethod.CASH)
    readiness = modification_readiness(order, FakeAttempts())
    assert readiness.editable is False
    assert readiness.requires_new_order is True


@pytest.mark.parametrize(
    "status",
    [
        OrderState.PAID,
        OrderState.CONFIRMED,
        OrderState.IN_PREPARATION,
        OrderState.READY,
        OrderState.DELIVERED,
        OrderState.PICKED_UP,
        OrderState.CANCELLED,
    ],
)
def test_closed_states_require_new_order(status):
    readiness = modification_readiness(make_order(status), FakeAttempts())
    assert readiness.editable is False
    assert readiness.requires_new_order is True


def test_prepare_keeps_draft_untouched():
    order = make_order()
    assert prepare_order_for_modification(order, FakeAttempts(), NOW) == []
    assert order.status is OrderState.DRAFT


def test_prepare_reopens_and_returns_superseded_attempt_ids():
    order = make_order(OrderState.PENDING, PaymentMethod.ONLINE)
    order.confirmed_at = datetime(2026, 9, 16, tzinfo=timezone.utc)
    attempts = FakeAttempts(has_approved=False)

    superseded = prepare_order_for_modification(order, attempts, NOW)

    assert order.status is OrderState.DRAFT
    assert order.confirmed_at is None
    assert attempts.superseded == [("o-1", 0, NOW)]
    assert superseded == ["attempt-1"]


def test_prepare_reopens_pending_without_payment_method():
    order = make_order(OrderState.PENDING, None)
    order.confirmed_at = datetime(2026, 9, 16, tzinfo=timezone.utc)

    prepare_order_for_modification(order, FakeAttempts(), NOW)

    assert order.status is OrderState.DRAFT
    assert order.confirmed_at is None


def test_prepare_rejects_cash_pending_without_touching_the_order():
    order = make_order(OrderState.PENDING, PaymentMethod.CASH)
    with pytest.raises(NewOrderRequiredError):
        prepare_order_for_modification(order, FakeAttempts(), NOW)
    assert order.status is OrderState.PENDING


def test_prepare_rejects_paid_order():
    order = make_order(OrderState.PAID, PaymentMethod.ONLINE)
    with pytest.raises(NewOrderRequiredError):
        prepare_order_for_modification(order, FakeAttempts(), NOW)
    assert order.status is OrderState.PAID
