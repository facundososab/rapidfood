import pytest
from decimal import Decimal
from datetime import date, datetime, timezone
from unittest.mock import Mock
from modules.order.application.use_cases.confirm_order_use_case import ConfirmOrderUseCase
from modules.order.application.ports.driver.confirm_order_ports import ConfirmOrderCommand
from modules.order.application.ports.driven.catalog_query import (
    VariantContext, ModifierGroupInfo, ModifierOptionInfo, IngredientInfo,
)
from modules.order.application.ports.driven.business_config_query import BusinessConfigSnapshot
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_line_modifier import OrderLineModifier
from modules.order.domain.models.order_origin import OrderOrigin
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.domain.errors.order_errors import (
    ModifierValidationError,
    OrderClientRequiredError,
    PaymentTypeRequiredError,
)


def make_order_with_line(modifier_option_ids=None, client_name="Cliente Test"):
    order = Order(
        id="o-1",
        status=OrderState.DRAFT,
        subtotal=Decimal("0"),
        discount=Decimal("0"),
        client_name=client_name,  # orders must be attributable to a client
        payment_type=PaymentMethod.ONLINE,  # RN-004: payment method is required
    )
    modifiers = []
    if modifier_option_ids:
        for opt_id in modifier_option_ids:
            modifiers.append(OrderLineModifier(
                id=f"m-{opt_id}",
                order_line_id="line-1",
                modifier_option_id=opt_id,
                option_name_snapshot="",
            ))
    line = OrderLine(
        id="line-1",
        order_id="o-1",
        product_variant_id="v-doble",
        quantity=2,
        unit_price=Decimal("11000"),
        subtotal=Decimal("22000"),
        modifiers=modifiers,
    )
    order.add_line(line)
    return order


def make_catalog_query(variant_price, modifier_groups=()):
    mock = Mock()
    mock.get_variant_context.return_value = VariantContext(
        product_id="p-1",
        product_name="Stacker",
        product_available=True,
        variant_id="v-doble",
        variant_name="Doble",
        variant_available=True,
        current_price=variant_price,
        ingredients=(),
        modifier_groups=modifier_groups,
    )
    return mock


def make_config_query(is_open=True, min_order=Decimal("0"), shipping=Decimal("0")):
    mock = Mock()
    mock.get_config.return_value = BusinessConfigSnapshot(
        is_open=is_open,
        min_order_amount=min_order,
        shipping_cost=shipping,
    )
    return mock


def test_confirm_requires_a_client():
    order = make_order_with_line(client_name=None)
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("12500")),
    )
    with pytest.raises(OrderClientRequiredError):
        uc.execute(ConfirmOrderCommand(order_id="o-1"))


def test_confirm_requires_a_payment_type():
    """RN-004/RN-023: confirming without a payment method must be rejected.

    Otherwise an agent order lands in PENDING with a NULL payment type, a state
    modification_readiness treats as closed (forcing a new order to pay).
    """
    order = make_order_with_line()
    order.payment_type = None
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("12500")),
    )
    with pytest.raises(PaymentTypeRequiredError):
        uc.execute(ConfirmOrderCommand(order_id="o-1"))

    # The order stays a DRAFT: it is not closed, just not confirmable yet.
    assert order.status is OrderState.DRAFT
    mock_repo.save.assert_not_called()


def test_confirm_freezes_prices():
    """
    Variant price at confirmation time (12500) replaces the draft price (11000).
    2 units: subtotal should be 25000.
    """
    order = make_order_with_line()
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("12500")),
    )
    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    frozen_line = order.lines[0]
    assert frozen_line.unit_price == Decimal("12500")
    assert frozen_line.subtotal == Decimal("25000")


def test_confirm_freezes_modifier_snapshot():
    extras_group = ModifierGroupInfo(
        group_id="g-extras",
        name="Extras",
        min_selections=0,
        max_selections=3,
        options=(
            ModifierOptionInfo(
                option_id="opt-bacon",
                name="Bacon",
                price_delta=Decimal("1000"),
                available=True,
            ),
        ),
    )
    order = make_order_with_line(modifier_option_ids=["opt-bacon"])
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(
            variant_price=Decimal("11500"),
            modifier_groups=(extras_group,),
        ),
    )
    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    modifier = order.lines[0].modifiers[0]
    assert modifier.option_name_snapshot == "Bacon"
    assert modifier.price_delta == Decimal("1000")
    # unit_price = 11500 (variant) + 1000 (bacon) = 12500
    assert order.lines[0].unit_price == Decimal("12500")
    # subtotal = 12500 * 2 = 25000
    assert order.lines[0].subtotal == Decimal("25000")


def test_confirm_sets_confirmed_at_and_confirms_a_manual_order():
    """A manual (in place) order is settled by the operator: it confirms to CONFIRMED."""
    order = make_order_with_line()
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("10000")),
    )
    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    assert order.confirmed_at is not None
    assert order.status.value == "CONFIRMED"


def test_confirm_keeps_an_agent_order_pending():
    """An agent order awaits settlement: it confirms to PENDING."""
    order = make_order_with_line()
    order.origin = OrderOrigin.AGENT
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("10000")),
    )
    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    assert order.status.value == "PENDING"


def test_confirm_retry_on_an_already_confirmed_order_is_idempotent():
    order = make_order_with_line()
    order.status = OrderState.PENDING
    order.confirmed_at = datetime(2026, 9, 17, tzinfo=timezone.utc)
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("10000")),
    )
    response = uc.execute(ConfirmOrderCommand(order_id="o-1"))

    assert response.status == "PENDING"
    assert response.confirmed_at is not None
    # No re-freeze / no state change on the retry.
    mock_repo.save.assert_not_called()


def test_confirm_rejects_a_cancelled_order():
    from modules.order.domain.errors.order_errors import OrderNotModifiableError

    order = make_order_with_line()
    order.status = OrderState.CANCELLED
    order.confirmed_at = datetime(2026, 9, 17, tzinfo=timezone.utc)
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("10000")),
    )
    with pytest.raises(OrderNotModifiableError):
        uc.execute(ConfirmOrderCommand(order_id="o-1"))


def test_confirm_recomputes_the_eta_with_fresh_demand():
    order = make_order_with_line()
    order.business_config_id = "b-1"
    order.route_duration_minutes = 12
    order.estimated_time = 999  # stale value from set_delivery time
    mock_repo = Mock()
    mock_repo.get_by_id.return_value = order

    class FakeEstimator:
        def estimate_minutes(self, business_config_id):
            return 25

    uc = ConfirmOrderUseCase(
        order_repo=mock_repo,
        config_query=make_config_query(),
        catalog_query=make_catalog_query(variant_price=Decimal("12500")),
        prep_time_estimator=FakeEstimator(),
    )

    uc.execute(ConfirmOrderCommand(order_id="o-1"))

    assert order.estimated_time == 37  # 25 (fresh prep) + 12 (route)
