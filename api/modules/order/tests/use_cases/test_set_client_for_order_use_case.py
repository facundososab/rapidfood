"""Attach the customer identity to a draft order."""
from decimal import Decimal

import pytest

from modules.order.application.ports.driver.set_client_for_order_port import (
    SetClientForOrderCommand,
)
from modules.order.application.use_cases.set_client_for_order_use_case import (
    SetClientForOrderUseCase,
)
from modules.order.domain.errors.order_errors import OrderNotFound, OrderNotModifiableError
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState


class FakeOrderRepo:
    def __init__(self, order):
        self.order = order
        self.saves = 0

    def get_by_id(self, order_id):
        return self.order

    def save(self, order):
        self.saves += 1
        return order


class FakeClientQuery:
    def __init__(self, exists=True):
        self.exists = exists
        self.calls = []

    def check_client_exists(self, client_id):
        self.calls.append(client_id)
        return self.exists


def _order(status=OrderState.DRAFT):
    return Order(id="o-1", status=status, subtotal=Decimal("0"), discount=Decimal("0"))


def test_sets_the_name_and_links_the_client():
    repo = FakeOrderRepo(_order())
    use_case = SetClientForOrderUseCase(repo, FakeClientQuery())

    result = use_case.execute(
        SetClientForOrderCommand(
            order_id="o-1", client_name="Facundo Sosa", client_id="client-1"
        )
    )

    assert result.client_name == "Facundo Sosa"
    assert result.client_id == "client-1"
    assert repo.order.client_name == "Facundo Sosa"
    assert repo.order.client_id == "client-1"


def test_name_only_keeps_the_order_attributable():
    repo = FakeOrderRepo(_order())
    use_case = SetClientForOrderUseCase(repo, FakeClientQuery())

    result = use_case.execute(
        SetClientForOrderCommand(order_id="o-1", client_name="Facundo")
    )

    assert result.client_id is None
    assert result.client_name == "Facundo"


def test_unknown_client_is_rejected():
    repo = FakeOrderRepo(_order())
    use_case = SetClientForOrderUseCase(repo, FakeClientQuery(exists=False))

    with pytest.raises(OrderNotFound):
        use_case.execute(
            SetClientForOrderCommand(order_id="o-1", client_id="ghost")
        )


def test_only_draft_orders_can_change_the_client():
    repo = FakeOrderRepo(_order(OrderState.PENDING))
    use_case = SetClientForOrderUseCase(repo, FakeClientQuery())

    with pytest.raises(OrderNotModifiableError):
        use_case.execute(
            SetClientForOrderCommand(order_id="o-1", client_name="Facundo")
        )
