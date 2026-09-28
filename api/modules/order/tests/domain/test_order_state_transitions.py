"""Centralized order state-transition rules (single source of truth)."""
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.domain.services.state_transitions import (
    CANCELLABLE_STATES,
    can_transition,
    is_cancellable,
)


def test_online_pending_can_become_paid():
    assert can_transition(
        OrderState.PENDING, OrderState.PAID, PaymentMethod.ONLINE
    ) is True


def test_cash_pending_can_become_confirmed():
    assert can_transition(
        OrderState.PENDING, OrderState.CONFIRMED, PaymentMethod.CASH
    ) is True


def test_cash_pending_cannot_become_paid():
    assert can_transition(
        OrderState.PENDING, OrderState.PAID, PaymentMethod.CASH
    ) is False


def test_online_pending_cannot_become_confirmed():
    assert can_transition(
        OrderState.PENDING, OrderState.CONFIRMED, PaymentMethod.ONLINE
    ) is False


def test_pending_without_payment_type_allows_both_settlements():
    # Legacy/manual orders never captured the payment method; the operator
    # decides how it was settled, so neither forward transition is blocked.
    assert can_transition(OrderState.PENDING, OrderState.PAID, None) is True
    assert can_transition(OrderState.PENDING, OrderState.CONFIRMED, None) is True
    assert can_transition(OrderState.PENDING, OrderState.CANCELLED, None) is True


def test_forward_transitions():
    assert can_transition(OrderState.PAID, OrderState.CONFIRMED, PaymentMethod.ONLINE)
    assert can_transition(OrderState.CONFIRMED, OrderState.IN_PREPARATION, PaymentMethod.CASH)
    assert can_transition(OrderState.IN_PREPARATION, OrderState.READY, None)
    assert can_transition(OrderState.READY, OrderState.DELIVERED, None)
    assert can_transition(OrderState.READY, OrderState.PICKED_UP, None)


def test_terminal_states_have_no_transitions():
    for terminal in (
        OrderState.DELIVERED,
        OrderState.PICKED_UP,
        OrderState.CANCELLED,
    ):
        assert can_transition(terminal, OrderState.PENDING, PaymentMethod.ONLINE) is False
        assert can_transition(terminal, OrderState.CONFIRMED, PaymentMethod.CASH) is False


def test_draft_can_start_confirm_or_cancel():
    assert can_transition(OrderState.DRAFT, OrderState.PENDING, None) is True
    # A manual (in place) draft is accepted by the operator straight away.
    assert can_transition(OrderState.DRAFT, OrderState.CONFIRMED, None) is True
    assert can_transition(OrderState.DRAFT, OrderState.CANCELLED, None) is True


def test_cancellable_states():
    assert CANCELLABLE_STATES == frozenset(
        {
            OrderState.DRAFT,
            OrderState.PENDING,
            OrderState.PAID,
            OrderState.CONFIRMED,
        }
    )
    for status in CANCELLABLE_STATES:
        assert is_cancellable(status) is True


def test_non_cancellable_states():
    for status in (
        OrderState.IN_PREPARATION,
        OrderState.READY,
        OrderState.DELIVERED,
        OrderState.PICKED_UP,
        OrderState.CANCELLED,
    ):
        assert is_cancellable(status) is False
