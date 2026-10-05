"""Reads (current order, latest active, summary) and set-pickup."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from modules.order.application.ports.driven.business_config_query import (
    BusinessConfigSnapshot,
)
from modules.order.application.ports.driver.get_current_order_port import (
    GetCurrentOrderQuery,
)
from modules.order.application.ports.driver.get_latest_active_order_port import (
    GetLatestActiveOrderQuery,
)
from modules.order.application.ports.driver.get_or_create_current_draft_port import (
    GetOrCreateCurrentDraftCommand,
)
from modules.order.application.ports.driver.set_pickup_for_order_port import (
    SetPickupForOrderCommand,
)
from modules.order.application.ports.driver.start_draft_order_ports import (
    StartDraftOrderCommand,
    StartDraftOrderResponse,
)
from modules.order.application.use_cases.get_current_order_use_case import (
    GetCurrentOrderUseCase,
)
from modules.order.application.use_cases.get_latest_active_order_use_case import (
    GetLatestActiveOrderUseCase,
)
from modules.order.application.use_cases.get_or_create_current_draft_use_case import (
    GetOrCreateCurrentDraftUseCase,
)
from modules.order.application.use_cases.get_order_summary_use_case import (
    GetOrderSummaryUseCase,
)
from modules.order.application.use_cases.set_pickup_for_order_use_case import (
    SetPickupForOrderUseCase,
)
from modules.order.domain.errors.order_errors import NewOrderRequiredError
from modules.order.domain.models.delivery_address import DeliveryAddress
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.tests.use_cases.fakes import (
    FakeAttempts,
    FakeClock,
    FakeExecutor,
    make_order,
    make_order_with_line,
)


class FakeOrderRepo:
    def __init__(self, orders=None):
        self.orders = list(orders or [])

    def get_by_id(self, order_id):
        return next((o for o in self.orders if o.id == order_id), None)

    def save(self, order):
        return order

    def list(self, order_filter=None):
        result = list(self.orders)
        f = order_filter
        if f is not None:
            if f.status is not None:
                result = [o for o in result if o.status is f.status]
            if f.status_in is not None:
                result = [o for o in result if o.status in f.status_in]
            if f.business_config_id is not None:
                result = [o for o in result if o.business_config_id == f.business_config_id]
            if f.conversation_id is not None:
                result = [o for o in result if o.conversation_id == f.conversation_id]
            if f.client_id is not None:
                result = [o for o in result if o.client_id == f.client_id]
        return result


class FakeConfigQuery:
    def __init__(self, min_order=Decimal("0")):
        self._min = min_order

    def get_config(self):
        return BusinessConfigSnapshot(
            is_open=True,
            shipping_cost=Decimal("0"),
            min_order_amount=self._min,
            business_config_id="b-1",
        )


class FakeStartDraft:
    def __init__(self):
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return StartDraftOrderResponse(order_id="new-order", status="DRAFT")


def _scoped(order, *, business="b-1", conversation="c-1", client=None):
    order.business_config_id = business
    order.conversation_id = conversation
    order.client_id = client
    return order


def test_current_order_prefers_the_draft():
    draft = _scoped(make_order(OrderState.DRAFT))
    pending = _scoped(make_order(OrderState.PENDING, PaymentMethod.ONLINE))
    use_case = GetCurrentOrderUseCase(FakeOrderRepo([pending, draft]), FakeAttempts())

    result = use_case.execute(
        GetCurrentOrderQuery(business_config_id="b-1", conversation_id="c-1")
    )

    assert result.found is True
    assert result.order is draft
    assert result.editable is True


def test_current_order_reports_a_reopenable_pending_online():
    pending = _scoped(make_order(OrderState.PENDING, PaymentMethod.ONLINE))
    use_case = GetCurrentOrderUseCase(
        FakeOrderRepo([pending]), FakeAttempts(has_approved=False)
    )

    result = use_case.execute(
        GetCurrentOrderQuery(business_config_id="b-1", conversation_id="c-1")
    )

    assert result.editable is True
    assert result.requires_reopen is True
    assert result.requires_new_order is False


def test_current_order_reports_new_order_required_for_paid():
    paid = _scoped(make_order(OrderState.PAID, PaymentMethod.ONLINE))
    use_case = GetCurrentOrderUseCase(FakeOrderRepo([paid]), FakeAttempts())

    result = use_case.execute(
        GetCurrentOrderQuery(business_config_id="b-1", conversation_id="c-1")
    )

    assert result.found is True
    assert result.editable is False
    assert result.requires_new_order is True


def test_current_order_not_found_for_an_unknown_conversation():
    use_case = GetCurrentOrderUseCase(FakeOrderRepo([]), FakeAttempts())
    result = use_case.execute(
        GetCurrentOrderQuery(business_config_id="b-1", conversation_id="missing")
    )
    assert result.found is False


def test_latest_active_order_prefers_the_client_scope():
    mine = _scoped(make_order(OrderState.CONFIRMED), client="client-1")
    other = _scoped(make_order(OrderState.READY), client="client-2")
    orders = _scoped(make_order(OrderState.DRAFT), client="client-1")
    use_case = GetLatestActiveOrderUseCase(FakeOrderRepo([other, mine, orders]))

    result = use_case.execute(
        GetLatestActiveOrderQuery(business_config_id="b-1", client_id="client-1")
    )

    assert result is mine


def test_latest_active_order_ignores_drafts_and_finished_orders():
    draft = _scoped(make_order(OrderState.DRAFT), client="client-1")
    delivered = _scoped(make_order(OrderState.DELIVERED), client="client-1")
    use_case = GetLatestActiveOrderUseCase(FakeOrderRepo([draft, delivered]))

    result = use_case.execute(
        GetLatestActiveOrderQuery(business_config_id="b-1", client_id="client-1")
    )

    assert result is None


def test_summary_lists_missing_requirements_for_a_draft():
    order = make_order_with_line()
    order.delivery_type = DeliveryType.DELIVERY
    order.delivery_address = None
    order.payment_type = None
    use_case = GetOrderSummaryUseCase(FakeOrderRepo([order]), FakeConfigQuery(Decimal("2000")))

    summary = use_case.execute(order.id)

    assert summary.order_id == order.id
    assert "delivery_address" in summary.missing_requirements
    assert "payment_type" in summary.missing_requirements
    assert "minimum_order_not_reached" in summary.missing_requirements
    assert summary.lines[0].line_id == order.lines[0].id


def test_summary_of_a_complete_delivery_order_has_no_missing_requirements():
    order = make_order_with_line()
    order.client_name = "Ana"
    order.delivery_type = DeliveryType.DELIVERY
    order.delivery_address = DeliveryAddress(
        street="San Juan", street_number="3250", city="Rosario", province="Santa Fe"
    )
    order.payment_type = PaymentMethod.CASH
    use_case = GetOrderSummaryUseCase(FakeOrderRepo([order]), FakeConfigQuery(Decimal("0")))

    summary = use_case.execute(order.id)

    assert summary.missing_requirements == []
    assert summary.address["street"] == "San Juan"


def test_summary_flags_an_empty_order():
    order = _scoped(make_order(OrderState.DRAFT))
    use_case = GetOrderSummaryUseCase(FakeOrderRepo([order]), FakeConfigQuery())

    summary = use_case.execute(order.id)

    assert "empty_order" in summary.missing_requirements


def test_get_or_create_current_draft_reuses_an_existing_draft():
    draft = _scoped(make_order(OrderState.DRAFT))
    start_draft = FakeStartDraft()
    use_case = GetOrCreateCurrentDraftUseCase(FakeOrderRepo([draft]), start_draft)

    result = use_case.execute(
        GetOrCreateCurrentDraftCommand(business_config_id="b-1", conversation_id="c-1")
    )

    assert result.order_id == draft.id
    assert result.created is False
    assert start_draft.commands == []


def test_get_or_create_current_draft_creates_when_none_exists():
    start_draft = FakeStartDraft()
    use_case = GetOrCreateCurrentDraftUseCase(FakeOrderRepo([]), start_draft)

    result = use_case.execute(
        GetOrCreateCurrentDraftCommand(
            business_config_id="b-1", conversation_id="c-1", client_name="Ana"
        )
    )

    assert result.order_id == "new-order"
    assert result.created is True
    assert start_draft.commands[0].conversation_id == "c-1"
    assert start_draft.commands[0].business_config_id == "b-1"


def test_get_or_create_current_draft_reuses_the_winner_after_a_race():
    """Parallel creates: the loser gets DuplicateActiveOrderError and reuses it.

    This is what keeps exactly ONE active order per conversation when two tool
    calls are emitted in the same agent turn.
    """
    from modules.order.domain.errors.order_errors import DuplicateActiveOrderError

    winner = _scoped(make_order(OrderState.DRAFT))

    class RacyRepo(FakeOrderRepo):
        def __init__(self):
            super().__init__([])
            self.list_calls = 0

        def list(self, order_filter=None):
            self.list_calls += 1
            # 1st read: no draft yet. After losing the race: the winner exists.
            return [] if self.list_calls == 1 else [winner]

    class LosingStartDraft:
        def execute(self, command):
            raise DuplicateActiveOrderError("lost the race")

    use_case = GetOrCreateCurrentDraftUseCase(RacyRepo(), LosingStartDraft())

    result = use_case.execute(
        GetOrCreateCurrentDraftCommand(business_config_id="b-1", conversation_id="c-1")
    )

    assert result.order_id == winner.id
    assert result.created is False


def test_set_pickup_clears_delivery_and_bumps_version():
    order = make_order_with_line()
    order.delivery_type = DeliveryType.DELIVERY
    order.delivery_address = DeliveryAddress(
        street="San Juan", street_number="3250", city="Rosario", province="Santa Fe"
    )
    order.shipping_cost = Decimal("350")
    executor = FakeExecutor(FakeAttempts())
    executor.register(order)
    use_case = SetPickupForOrderUseCase(executor=executor, clock=FakeClock())

    result = use_case.execute(
        SetPickupForOrderCommand(
            business_config_id="b-1", order_id="o-1", external_message_id="m-1"
        )
    )

    assert order.delivery_type is DeliveryType.PICKUP
    assert order.delivery_address is None
    assert order.shipping_cost == 0
    assert result.version == 1


def test_set_pickup_sets_eta_to_preparation_only():
    order = make_order_with_line()
    executor = FakeExecutor(FakeAttempts())
    executor.register(order)

    class FakeEstimator:
        def estimate_minutes(self, business_config_id):
            return 25

    use_case = SetPickupForOrderUseCase(
        executor=executor, clock=FakeClock(), prep_time_estimator=FakeEstimator()
    )

    use_case.execute(
        SetPickupForOrderCommand(
            business_config_id="b-1", order_id="o-1", external_message_id="m-1"
        )
    )

    assert order.estimated_time == 25
    assert order.route_duration_minutes is None


def test_set_pickup_reopens_pending_online():
    order = make_order_with_line(status=OrderState.PENDING, payment_type=PaymentMethod.ONLINE)
    attempts = FakeAttempts(has_approved=False)
    executor = FakeExecutor(attempts)
    executor.register(order)
    use_case = SetPickupForOrderUseCase(executor=executor, clock=FakeClock())

    use_case.execute(
        SetPickupForOrderCommand(
            business_config_id="b-1", order_id="o-1", external_message_id="m-1"
        )
    )

    assert order.status is OrderState.DRAFT
    assert attempts.superseded


def test_set_pickup_rejects_a_paid_order():
    order = make_order_with_line(status=OrderState.PAID, payment_type=PaymentMethod.ONLINE)
    executor = FakeExecutor(FakeAttempts())
    executor.register(order)
    use_case = SetPickupForOrderUseCase(executor=executor, clock=FakeClock())

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(
            SetPickupForOrderCommand(
                business_config_id="b-1", order_id="o-1", external_message_id="m-1"
            )
        )
