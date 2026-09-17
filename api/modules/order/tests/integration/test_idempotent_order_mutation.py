"""Integration tests for the atomic idempotency executor (requires the test DB).

Proves the claim + mutation + result persistence happen together and that a
retry replays the stored result without executing the mutation again.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from modules.order.infrastructure.adapters.driven.prisma.idempotent_order_mutation import (
    PrismaIdempotentOrderMutation,
)

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _clean(db):
    yield
    db.idempotentoperation.delete_many(where={})
    db.order.delete_many(where={})


def _seed(db) -> tuple[str, str]:
    business_id = str(uuid4())
    order_id = str(uuid4())
    db.businessconfiguration.create(
        {
            "id": business_id,
            "businessName": "Idempotency Test Biz",
            "minOrder": Decimal("0"),
            "shippingCost": Decimal("0"),
        }
    )
    db.order.create(
        {
            "id": order_id,
            "status": "DRAFT",
            "origin": "AGENT",
            "subtotal": Decimal("0"),
            "discount": Decimal("0"),
            "businessConfigId": business_id,
        }
    )
    return business_id, order_id


def test_retry_replays_stored_result_without_reexecuting(db) -> None:
    business_id, order_id = _seed(db)
    executor = PrismaIdempotentOrderMutation(db)
    calls = {"n": 0}

    def mutate(ctx):
        calls["n"] += 1
        ctx.order.client_name = "Idempotent"
        return {"line_id": "line-abc"}

    first = executor.execute(
        business_config_id=business_id,
        idempotency_key="key-1",
        operation_name="add_item",
        order_id=order_id,
        mutate=mutate,
    )
    assert first.replayed is False
    assert first.result == {"line_id": "line-abc"}

    second = executor.execute(
        business_config_id=business_id,
        idempotency_key="key-1",
        operation_name="add_item",
        order_id=order_id,
        mutate=mutate,
    )
    assert second.replayed is True
    assert second.result == {"line_id": "line-abc"}
    assert calls["n"] == 1
    assert db.idempotentoperation.count(where={"businessConfigId": business_id}) == 1


def test_distinct_keys_apply_separately(db) -> None:
    business_id, order_id = _seed(db)
    executor = PrismaIdempotentOrderMutation(db)
    calls = {"n": 0}

    def mutate(ctx):
        calls["n"] += 1
        return {"n": calls["n"]}

    executor.execute(
        business_config_id=business_id,
        idempotency_key="key-a",
        operation_name="add_item",
        order_id=order_id,
        mutate=mutate,
    )
    second = executor.execute(
        business_config_id=business_id,
        idempotency_key="key-b",
        operation_name="add_item",
        order_id=order_id,
        mutate=mutate,
    )

    assert second.replayed is False
    assert calls["n"] == 2
    assert db.idempotentoperation.count(where={"businessConfigId": business_id}) == 2


def test_mutation_result_is_persisted_with_the_order(db) -> None:
    business_id, order_id = _seed(db)
    executor = PrismaIdempotentOrderMutation(db)

    executor.execute(
        business_config_id=business_id,
        idempotency_key="key-1",
        operation_name="set_delivery",
        order_id=order_id,
        mutate=lambda ctx: (setattr(ctx.order, "client_name", "Persisted"), {"ok": True})[1],
    )

    row = db.order.find_unique(where={"id": order_id})
    assert row is not None
    assert row.clientName == "Persisted"
