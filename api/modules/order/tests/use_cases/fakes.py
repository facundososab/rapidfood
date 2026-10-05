"""Shared fakes for order application tests (no DB).

``FakePaymentCredentialsQuery`` never touches the linkage module: like the real
app-level adapter it answers with a plain token or ``None``, and it can be
configured to fail so the fallback paths can be asserted.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from modules.order.application.ports.driven.catalog_query import (
    IngredientInfo,
    ModifierGroupInfo,
    ModifierOptionInfo,
    VariantContext,
)
from modules.order.application.ports.driven.idempotency import (
    IdempotentMutationOutcome,
    OrderMutationContext,
)
from modules.order.application.ports.driven.payment_credentials_query import (
    PaymentCredentialsQuery,
)
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState

FIXED_NOW = datetime(2026, 9, 17, 12, 0, tzinfo=timezone.utc)


class FakeClock:
    def now(self) -> datetime:
        return FIXED_NOW


class FakeAttempts:
    """Fake PaymentAttemptQueryPort."""

    def __init__(self, has_approved: bool = False) -> None:
        self.has_approved = has_approved
        self.superseded: list[tuple[str, int, datetime]] = []

    def has_current_approved(self, order_id: str, version: int) -> bool:
        return self.has_approved

    def current_for_version(self, order_id: str, version: int):
        return None

    def supersede_current(self, order_id: str, version: int, at: datetime) -> list[str]:
        self.superseded.append((order_id, version, at))
        return ["attempt-1"]


class FakeCatalog:
    """Fake CatalogQuery returning one sellable variant."""

    def get_variant_context(self, variant_id: str) -> VariantContext:
        return VariantContext(
            product_id="p-1",
            product_name="Stacker",
            product_available=True,
            variant_id=variant_id,
            variant_name="Doble",
            variant_available=True,
            current_price=Decimal("1000"),
            ingredients=(
                IngredientInfo("ing-removable", "Cebolla", True),
                IngredientInfo("ing-fixed", "Queso", False),
            ),
            modifier_groups=(
                ModifierGroupInfo(
                    "g-1",
                    "Extras",
                    0,
                    3,
                    (ModifierOptionInfo("opt-bacon", "Bacon", Decimal("200"), True),),
                ),
            ),
        )


class FakeCouponHistory:
    """Fake AppliedCouponRepositoryPort."""

    def __init__(self) -> None:
        self.records: list = []

    def add(self, snapshot):
        self.records.append(snapshot)
        return snapshot

    def list_by_coupon(self, coupon_id: str):
        return [r for r in self.records if r.coupon_id == coupon_id]


class FakeDeliveryQuote:
    """Fake DeliveryQuoteQuery."""

    def __init__(self, available: bool = True, shipping_cost=Decimal("350")):
        self.available = available
        self.shipping_cost = shipping_cost
        self.calls = 0

    def quote(self, business_config_id, destination):
        from modules.order.application.ports.driven.delivery_quote_query import (
            DeliveryQuoteSnapshot,
        )

        self.calls += 1
        return DeliveryQuoteSnapshot(
            available=self.available,
            shipping_cost=self.shipping_cost if self.available else None,
            distance_km=3.2,
            estimated_duration_minutes=12.0,
            demand_level="LOW",
        )


class FakeCouponQuery:
    """Fake CouponQueryPort."""

    def __init__(self, valid: bool = True, discount=Decimal("500")):
        self.valid = valid
        self.discount = discount
        self.calls = 0

    def validate_coupon(self, coupon_code: str, order_subtotal):
        from modules.order.application.ports.driven.coupon_query import CouponSnapshot

        self.calls += 1
        if not self.valid:
            return None
        return CouponSnapshot(
            coupon_code=coupon_code,
            discount_amount=self.discount,
            is_valid=True,
            coupon_id="coupon-1",
            coupon_type="FIXED_AMOUNT",
            amount=Decimal("500"),
            available_uses=10,
        )


class FakeExecutor:
    """In-memory IdempotentOrderMutationPort with replay semantics."""

    def __init__(self, attempts: FakeAttempts, coupon_history=None) -> None:
        self.attempts = attempts
        self.coupon_history = coupon_history or FakeCouponHistory()
        self.orders: dict[str, Order] = {}
        self.results: dict[str, dict] = {}
        self.calls = 0

    def register(self, order: Order) -> None:
        self.orders[order.id] = order

    def execute(
        self,
        *,
        business_config_id: str,
        idempotency_key: str,
        operation_name: str,
        order_id: str,
        mutate,
    ) -> IdempotentMutationOutcome:
        if idempotency_key in self.results:
            return IdempotentMutationOutcome(
                replayed=True, result=self.results[idempotency_key]
            )
        self.calls += 1
        order = self.orders[order_id]
        ctx = OrderMutationContext(
            order=order,
            attempts=self.attempts,
            coupon_history=self.coupon_history,
        )
        result = mutate(ctx)
        self.results[idempotency_key] = result
        return IdempotentMutationOutcome(
            replayed=False,
            result=result,
            superseded_attempt_ids=tuple(ctx.superseded_attempt_ids),
        )


class FakePaymentCredentialsQuery(PaymentCredentialsQuery):
    """In-memory PaymentCredentialsQuery that records the requested businesses."""

    def __init__(
        self,
        tokens: Optional[dict[str, str]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        self.tokens = dict(tokens or {})
        self.error = error
        self.requested: list[str] = []

    def get_access_token(self, business_config_id: str) -> Optional[str]:
        self.requested.append(business_config_id)
        if self.error is not None:
            raise self.error
        return self.tokens.get(business_config_id)


def make_order(status=OrderState.DRAFT, payment_type=None, version=0) -> Order:
    return Order(
        id="o-1",
        status=status,
        subtotal=Decimal("0"),
        discount=Decimal("0"),
        payment_type=payment_type,
        version=version,
    )


def make_order_with_line(
    *,
    line_id: str = "line-1",
    variant_id: str = "v-1",
    quantity: int = 1,
    unit_price: Decimal = Decimal("1000"),
    status=OrderState.DRAFT,
    payment_type=None,
    version: int = 0,
) -> Order:
    from modules.order.domain.models.order_line import OrderLine

    order = make_order(status, payment_type, version)
    order.lines.append(
        OrderLine(
            id=line_id,
            order_id=order.id,
            product_variant_id=variant_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=unit_price * quantity,
        )
    )
    order.subtotal = unit_price * quantity
    return order
