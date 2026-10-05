"""Reopen-aware, idempotent set-delivery and apply-coupon use cases (fakes)."""
import pytest

from modules.order.application.ports.driver.apply_coupon_to_order_port import (
    ApplyCouponToOrderCommand,
)
from modules.order.application.ports.driver.set_delivery_for_order_port import (
    SetDeliveryForOrderCommand,
)
from modules.order.application.use_cases.apply_coupon_to_order_use_case import (
    ApplyCouponToOrderUseCase,
)
from modules.order.application.use_cases.set_delivery_for_order_use_case import (
    SetDeliveryForOrderUseCase,
)
from modules.order.domain.errors.order_errors import (
    DeliveryAddressRequiredError,
    DeliveryNotAvailableError,
    InvalidCouponError,
    NewOrderRequiredError,
)
from modules.order.domain.models.delivery_type import DeliveryType
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.tests.use_cases.fakes import (
    FakeAttempts,
    FakeClock,
    FakeCouponQuery,
    FakeDeliveryQuote,
    FakeExecutor,
    make_order_with_line,
)


def _delivery_use_case(order, *, quote=None, attempts=None):
    attempts = attempts or FakeAttempts()
    executor = FakeExecutor(attempts)
    executor.register(order)
    quote = quote or FakeDeliveryQuote()
    use_case = SetDeliveryForOrderUseCase(
        delivery_quote=quote, executor=executor, clock=FakeClock()
    )
    return use_case, executor, quote, attempts


def _coupon_use_case(order, *, coupon=None, attempts=None):
    attempts = attempts or FakeAttempts()
    executor = FakeExecutor(attempts)
    executor.register(order)
    coupon = coupon or FakeCouponQuery()
    use_case = ApplyCouponToOrderUseCase(
        coupon_query=coupon, executor=executor, clock=FakeClock()
    )
    return use_case, executor, coupon


def _delivery_command(**overrides):
    base = dict(
        business_config_id="b-1",
        order_id="o-1",
        external_message_id="m-1",
        street="San Juan",
        street_number="3250",
        city="Rosario",
        province="Santa Fe",
        conversation_id="c-1",
    )
    base.update(overrides)
    return SetDeliveryForOrderCommand(**base)


def _coupon_command(**overrides):
    base = dict(
        business_config_id="b-1",
        order_id="o-1",
        external_message_id="m-1",
        coupon_code="VERANO20",
        conversation_id="c-1",
    )
    base.update(overrides)
    return ApplyCouponToOrderCommand(**base)


def test_delivery_sets_the_snapshot_and_shipping_cost():
    order = make_order_with_line()
    use_case, _, quote, _ = _delivery_use_case(order)

    result = use_case.execute(_delivery_command())

    assert order.delivery_type is DeliveryType.DELIVERY
    assert order.delivery_address.street == "San Juan"
    assert order.shipping_cost == 350
    assert result.shipping_cost == "350"
    assert result.version == 1
    assert quote.calls == 1


def test_delivery_sets_eta_to_preparation_plus_route():
    order = make_order_with_line()
    attempts = FakeAttempts()
    executor = FakeExecutor(attempts)
    executor.register(order)

    class FakeEstimator:
        def estimate_minutes(self, business_config_id):
            return 25

    use_case = SetDeliveryForOrderUseCase(
        delivery_quote=FakeDeliveryQuote(),
        executor=executor,
        clock=FakeClock(),
        prep_time_estimator=FakeEstimator(),
    )

    use_case.execute(_delivery_command())

    assert order.route_duration_minutes == 12  # round(12.0)
    assert order.estimated_time == 37  # 25 + 12


def test_delivery_reopens_pending_online():
    order = make_order_with_line(status=OrderState.PENDING, payment_type=PaymentMethod.ONLINE)
    attempts = FakeAttempts(has_approved=False)
    use_case, _, _, _ = _delivery_use_case(order, attempts=attempts)

    use_case.execute(_delivery_command())

    assert order.status is OrderState.DRAFT
    assert attempts.superseded


def test_unavailable_delivery_does_not_touch_the_order():
    order = make_order_with_line()
    use_case, _, _, _ = _delivery_use_case(order, quote=FakeDeliveryQuote(available=False))

    with pytest.raises(DeliveryNotAvailableError):
        use_case.execute(_delivery_command())

    assert order.delivery_type is None
    assert order.shipping_cost is None


def test_delivery_requires_a_complete_address():
    order = make_order_with_line()
    use_case, _, _, _ = _delivery_use_case(order)

    with pytest.raises(DeliveryAddressRequiredError):
        use_case.execute(_delivery_command(street=""))


def test_delivery_rejects_a_paid_order():
    order = make_order_with_line(status=OrderState.PAID, payment_type=PaymentMethod.ONLINE)
    use_case, _, _, _ = _delivery_use_case(order)

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(_delivery_command())


def test_delivery_replay_does_not_reapply():
    order = make_order_with_line()
    use_case, executor, quote, _ = _delivery_use_case(order)

    use_case.execute(_delivery_command())
    second = use_case.execute(_delivery_command())

    assert second.replayed is True
    # The quote is resolved before the idempotency claim (it is a read-only
    # external computation), so a retry may quote again — but the mutation is
    # applied exactly once.
    assert quote.calls == 2
    assert executor.calls == 1


def test_coupon_applies_the_backend_discount_and_records_history():
    order = make_order_with_line()
    use_case, executor, _ = _coupon_use_case(order)

    result = use_case.execute(_coupon_command())

    assert order.coupon_code == "VERANO20"
    assert order.discount == 500
    assert result.discount_applied == "500"
    assert result.version == 1
    assert len(executor.coupon_history.records) == 1


def test_invalid_coupon_is_a_business_error():
    order = make_order_with_line()
    use_case, _, _ = _coupon_use_case(order, coupon=FakeCouponQuery(valid=False))

    with pytest.raises(InvalidCouponError):
        use_case.execute(_coupon_command())

    assert order.coupon_code is None


def test_coupon_on_an_empty_order_is_rejected():
    order = make_order_with_line()
    order.lines = []
    use_case, _, _ = _coupon_use_case(order)

    with pytest.raises(InvalidCouponError):
        use_case.execute(_coupon_command())


def test_coupon_replay_does_not_record_history_twice():
    order = make_order_with_line()
    use_case, executor, _ = _coupon_use_case(order)

    use_case.execute(_coupon_command())
    second = use_case.execute(_coupon_command())

    assert second.replayed is True
    assert executor.calls == 1
    assert len(executor.coupon_history.records) == 1


def test_coupon_reopens_pending_online():
    order = make_order_with_line(status=OrderState.PENDING, payment_type=PaymentMethod.ONLINE)
    attempts = FakeAttempts(has_approved=False)
    use_case, _, _ = _coupon_use_case(order, attempts=attempts)

    use_case.execute(_coupon_command())

    assert order.status is OrderState.DRAFT
    assert attempts.superseded
