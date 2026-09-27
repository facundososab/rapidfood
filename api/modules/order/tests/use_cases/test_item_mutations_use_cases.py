"""Reopen-aware, idempotent update-item and remove-item use cases (fakes)."""
import pytest

from modules.order.application.ports.driver.remove_item_from_order_port import (
    RemoveItemFromOrderCommand,
)
from modules.order.application.ports.driver.update_item_in_order_port import (
    UpdateItemInOrderCommand,
)
from modules.order.application.use_cases.remove_item_from_order_use_case import (
    RemoveItemFromOrderUseCase,
)
from modules.order.application.use_cases.update_item_in_order_use_case import (
    UpdateItemInOrderUseCase,
)
from modules.order.domain.errors.order_errors import (
    InvalidLineError,
    NewOrderRequiredError,
)
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.tests.use_cases.fakes import (
    FakeAttempts,
    FakeCatalog,
    FakeClock,
    FakeExecutor,
    make_order_with_line,
)


def _update_use_case(order, attempts=None):
    attempts = attempts or FakeAttempts()
    executor = FakeExecutor(attempts)
    executor.register(order)
    use_case = UpdateItemInOrderUseCase(
        catalog_query=FakeCatalog(), executor=executor, clock=FakeClock()
    )
    return use_case, executor, attempts


def _remove_use_case(order, attempts=None):
    attempts = attempts or FakeAttempts()
    executor = FakeExecutor(attempts)
    executor.register(order)
    use_case = RemoveItemFromOrderUseCase(executor=executor, clock=FakeClock())
    return use_case, executor, attempts


def _update_command(**overrides):
    base = dict(
        business_config_id="b-1",
        order_id="o-1",
        line_id="line-1",
        external_message_id="m-1",
        conversation_id="c-1",
    )
    base.update(overrides)
    return UpdateItemInOrderCommand(**base)


def _remove_command(**overrides):
    base = dict(
        business_config_id="b-1",
        order_id="o-1",
        line_id="line-1",
        external_message_id="m-1",
        conversation_id="c-1",
    )
    base.update(overrides)
    return RemoveItemFromOrderCommand(**base)


def test_update_changes_quantity_and_bumps_version():
    order = make_order_with_line(quantity=1)
    use_case, _, _ = _update_use_case(order)

    result = use_case.execute(_update_command(quantity=3))

    assert order.lines[0].quantity == 3
    assert order.lines[0].subtotal == 3000
    assert result.version == 1


def test_update_replaces_modifiers_and_recomputes_price():
    order = make_order_with_line()
    use_case, _, _ = _update_use_case(order)

    use_case.execute(_update_command(modifier_option_ids=["opt-bacon"]))

    line = order.lines[0]
    assert line.unit_price == 1200
    assert [m.modifier_option_id for m in line.modifiers] == ["opt-bacon"]


def test_update_can_clear_modifiers_with_an_empty_list():
    order = make_order_with_line()
    order.lines[0].modifiers = []
    use_case, _, _ = _update_use_case(order)

    use_case.execute(_update_command(modifier_option_ids=[]))

    assert order.lines[0].modifiers == []


def test_update_reopens_pending_online():
    order = make_order_with_line(status=OrderState.PENDING, payment_type=PaymentMethod.ONLINE)
    attempts = FakeAttempts(has_approved=False)
    use_case, _, _ = _update_use_case(order, attempts)

    use_case.execute(_update_command(quantity=2))

    assert order.status is OrderState.DRAFT
    assert order.lines[0].quantity == 2
    assert attempts.superseded


def test_update_rejects_paid_order():
    order = make_order_with_line(status=OrderState.PAID, payment_type=PaymentMethod.ONLINE)
    use_case, _, _ = _update_use_case(order)

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(_update_command(quantity=2))

    assert order.lines[0].quantity == 1


def test_update_rejects_unknown_line():
    order = make_order_with_line()
    use_case, _, _ = _update_use_case(order)

    with pytest.raises(InvalidLineError):
        use_case.execute(_update_command(line_id="missing"))


def test_update_replay_does_not_apply_twice():
    order = make_order_with_line(quantity=1)
    use_case, executor, _ = _update_use_case(order)

    use_case.execute(_update_command(quantity=2))
    second = use_case.execute(_update_command(quantity=2))

    assert second.replayed is True
    assert order.lines[0].quantity == 2
    assert executor.calls == 1


def test_remove_deletes_the_line():
    order = make_order_with_line()
    use_case, _, _ = _remove_use_case(order)

    result = use_case.execute(_remove_command())

    assert order.lines == []
    assert result.line_count == 0
    assert result.version == 1


def test_remove_reopens_pending_online():
    order = make_order_with_line(status=OrderState.PENDING, payment_type=PaymentMethod.ONLINE)
    attempts = FakeAttempts(has_approved=False)
    use_case, _, _ = _remove_use_case(order, attempts)

    use_case.execute(_remove_command())

    assert order.status is OrderState.DRAFT
    assert order.lines == []
    assert attempts.superseded


def test_remove_rejects_cash_pending():
    order = make_order_with_line(status=OrderState.PENDING, payment_type=PaymentMethod.CASH)
    use_case, _, _ = _remove_use_case(order)

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(_remove_command())

    assert len(order.lines) == 1


def test_remove_rejects_unknown_line():
    order = make_order_with_line()
    use_case, _, _ = _remove_use_case(order)

    with pytest.raises(InvalidLineError):
        use_case.execute(_remove_command(line_id="missing"))


def test_remove_replay_does_not_delete_twice():
    order = make_order_with_line()
    use_case, executor, _ = _remove_use_case(order)

    use_case.execute(_remove_command())
    second = use_case.execute(_remove_command())

    assert second.replayed is True
    assert executor.calls == 1
