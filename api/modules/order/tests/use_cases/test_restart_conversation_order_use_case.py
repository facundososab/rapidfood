"""Restart a conversation's order: close the unfinished one, open a fresh draft."""
from decimal import Decimal

from modules.order.application.ports.driver.restart_conversation_order_port import (
    RestartConversationOrderCommand,
)
from modules.order.application.ports.driver.start_draft_order_ports import (
    StartDraftOrderResponse,
)
from modules.order.application.use_cases.restart_conversation_order_use_case import (
    RestartConversationOrderUseCase,
)
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


class InMemoryOrderRepo:
    def __init__(self, orders=None):
        self.orders = list(orders or [])

    def get_by_id(self, order_id):
        return next((o for o in self.orders if o.id == order_id), None)

    def save(self, order):
        for index, existing in enumerate(self.orders):
            if existing.id == order.id:
                self.orders[index] = order
                return order
        self.orders.append(order)
        return order

    def list(self, order_filter=None):
        result = list(self.orders)
        f = order_filter
        if f is not None:
            if f.status is not None:
                result = [o for o in result if o.status is f.status]
            if f.business_config_id is not None:
                result = [o for o in result if o.business_config_id == f.business_config_id]
            if f.conversation_id is not None:
                result = [o for o in result if o.conversation_id == f.conversation_id]
        return result


class RecordingStartDraft:
    def __init__(self):
        self.commands = []
        self.calls = 0

    def execute(self, command):
        self.calls += 1
        self.commands.append(command)
        return StartDraftOrderResponse(order_id=f"draft-{self.calls}", status="DRAFT")


def _order(order_id="o-1", status=OrderState.DRAFT, payment=None):
    return Order(
        id=order_id,
        status=status,
        subtotal=Decimal("0"),
        discount=Decimal("0"),
        business_config_id="b-1",
        conversation_id="c-1",
        payment_type=payment,
    )


def _command():
    return RestartConversationOrderCommand(
        business_config_id="b-1", conversation_id="c-1"
    )


def test_restart_closes_the_draft_and_opens_a_fresh_agent_draft():
    old = _order(status=OrderState.DRAFT)
    repo = InMemoryOrderRepo([old])
    start = RecordingStartDraft()

    result = RestartConversationOrderUseCase(repo, start).execute(_command())

    assert old.status is OrderState.CANCELLED
    assert result.previous_order_id == "o-1"
    assert result.order_id == "draft-1"
    assert result.created is True
    # The new draft belongs to the agent channel (settlement is awaited).
    assert start.commands[0].origin == "AGENT"
    assert start.commands[0].conversation_id == "c-1"


def test_restart_also_closes_an_unpaid_pending_order():
    pending = _order(status=OrderState.PENDING, payment=PaymentMethod.ONLINE)
    repo = InMemoryOrderRepo([pending])
    start = RecordingStartDraft()

    result = RestartConversationOrderUseCase(repo, start).execute(_command())

    assert pending.status is OrderState.CANCELLED
    assert result.created is True
    assert start.calls == 1


def test_restart_is_a_noop_when_no_session_order_is_open():
    confirmed = _order(status=OrderState.CONFIRMED)
    repo = InMemoryOrderRepo([confirmed])
    start = RecordingStartDraft()

    result = RestartConversationOrderUseCase(repo, start).execute(_command())

    assert result.previous_order_id is None
    assert result.order_id is None
    assert result.created is False
    # An accepted/preparing order is real work in flight: never touched.
    assert confirmed.status is OrderState.CONFIRMED
    assert start.calls == 0
