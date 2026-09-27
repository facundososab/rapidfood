"""Reopen-aware, idempotent add-item use case (unit, fakes only)."""
import pytest

from modules.order.application.ports.driver.add_item_to_order_port import (
    AddItemToOrderCommand,
)
from modules.order.application.use_cases.add_item_to_order_use_case import (
    AddItemToOrderUseCase,
)
from modules.order.domain.errors.order_errors import (
    IngredientNotRemovableError,
    InvalidLineError,
    ModifierValidationError,
    NewOrderRequiredError,
)
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.tests.use_cases.fakes import (
    FakeAttempts,
    FakeCatalog,
    FakeClock,
    FakeExecutor,
    make_order,
)


def _command(**overrides) -> AddItemToOrderCommand:
    base = dict(
        business_config_id="b-1",
        order_id="o-1",
        product_variant_id="v-1",
        quantity=1,
        external_message_id="m-1",
        conversation_id="c-1",
    )
    base.update(overrides)
    return AddItemToOrderCommand(**base)


def _use_case(order, attempts=None):
    attempts = attempts or FakeAttempts()
    executor = FakeExecutor(attempts)
    executor.register(order)
    use_case = AddItemToOrderUseCase(
        catalog_query=FakeCatalog(), executor=executor, clock=FakeClock()
    )
    return use_case, executor, attempts


def test_adds_a_line_to_a_draft():
    order = make_order()
    use_case, _, _ = _use_case(order)

    result = use_case.execute(_command())

    assert result.replayed is False
    assert result.line_count == 1
    assert result.version == 1
    assert order.status is OrderState.DRAFT
    assert order.lines[0].quantity == 1


def test_reopens_pending_online_and_adds():
    order = make_order(OrderState.PENDING, PaymentMethod.ONLINE)
    attempts = FakeAttempts(has_approved=False)
    use_case, _, _ = _use_case(order, attempts)

    result = use_case.execute(_command())

    assert order.status is OrderState.DRAFT
    assert len(order.lines) == 1
    assert result.version == 1
    assert attempts.superseded and attempts.superseded[0][1] == 0


def test_adds_an_extra_line_with_modifiers_and_removed_ingredients():
    order = make_order()
    use_case, _, _ = _use_case(order)

    result = use_case.execute(
        _command(modifier_option_ids=["opt-bacon"], removed_ingredient_ids=["ing-removable"])
    )

    line = order.lines[0]
    assert line.unit_price == 1200
    assert line.modifiers[0].modifier_option_id == "opt-bacon"
    assert line.removed_ingredients[0].ingredient_id == "ing-removable"
    assert result.line_count == 1


def test_rejects_cash_pending_without_touching_the_order():
    order = make_order(OrderState.PENDING, PaymentMethod.CASH)
    use_case, _, _ = _use_case(order)

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(_command())

    assert order.lines == []
    assert order.status is OrderState.PENDING


def test_rejects_paid_order():
    order = make_order(OrderState.PAID, PaymentMethod.ONLINE)
    use_case, _, _ = _use_case(order)

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(_command())

    assert order.lines == []


def test_retry_with_the_same_message_does_not_duplicate_the_line():
    order = make_order()
    use_case, executor, _ = _use_case(order)

    first = use_case.execute(_command())
    second = use_case.execute(_command())

    assert first.replayed is False
    assert second.replayed is True
    assert second.line_id == first.line_id
    assert len(order.lines) == 1
    assert executor.calls == 1


def test_a_different_message_adds_a_second_line():
    order = make_order()
    use_case, _, _ = _use_case(order)

    use_case.execute(_command(external_message_id="m-1"))
    use_case.execute(_command(external_message_id="m-2"))

    assert len(order.lines) == 2


def test_non_removable_ingredient_is_rejected():
    order = make_order()
    use_case, _, _ = _use_case(order)

    with pytest.raises(IngredientNotRemovableError):
        use_case.execute(_command(removed_ingredient_ids=["ing-fixed"]))


def test_unknown_modifier_is_rejected():
    order = make_order()
    use_case, _, _ = _use_case(order)

    with pytest.raises(ModifierValidationError):
        use_case.execute(_command(modifier_option_ids=["opt-unknown"]))


def test_unknown_variant_is_rejected():
    class _NoVariantCatalog(FakeCatalog):
        def get_variant_context(self, variant_id):
            return None

    executor = FakeExecutor(FakeAttempts())
    executor.register(make_order())
    use_case = AddItemToOrderUseCase(
        catalog_query=_NoVariantCatalog(), executor=executor, clock=FakeClock()
    )
    with pytest.raises(InvalidLineError):
        use_case.execute(_command())


def test_unavailable_variant_is_rejected():
    import dataclasses

    class _NotSellableCatalog(FakeCatalog):
        def get_variant_context(self, variant_id):
            return dataclasses.replace(
                super().get_variant_context(variant_id), variant_available=False
            )

    executor = FakeExecutor(FakeAttempts())
    executor.register(make_order())
    use_case = AddItemToOrderUseCase(
        catalog_query=_NotSellableCatalog(), executor=executor, clock=FakeClock()
    )
    with pytest.raises(InvalidLineError):
        use_case.execute(_command())
