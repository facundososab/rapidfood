from modules.order.application.ports.driven.client_query import ClientQuery
from modules.order.application.ports.driven.catalog_query import (
    CatalogQuery, VariantContext, IngredientInfo, ModifierGroupInfo, ModifierOptionInfo,
)
from modules.order.application.ports.driven.business_config_query import (
    BusinessConfigQueryPort, BusinessConfigSnapshot,
)
from modules.order.application.ports.driven.coupon_query import CouponQueryPort, CouponSnapshot
from typing import Optional
from decimal import Decimal


class FakeClientQuery(ClientQuery):
    def check_client_exists(self, client_id: str) -> bool:
        return True


class FakeCatalogQuery(CatalogQuery):
    """Returns a simple variant context suitable for tests."""

    def get_variant_context(self, variant_id: str) -> Optional[VariantContext]:
        return VariantContext(
            product_id="fake-product-id",
            product_name="Fake Product",
            product_available=True,
            variant_id=variant_id,
            variant_name="Default",
            variant_available=True,
            current_price=Decimal("150.00"),
            ingredients=(),
            modifier_groups=(),
        )


class FakeBusinessConfigQuery(BusinessConfigQueryPort):
    def get_config(self) -> BusinessConfigSnapshot:
        return BusinessConfigSnapshot(
            is_open=True,
            shipping_cost=Decimal("50.00"),
            min_order_amount=Decimal("300.00"),
        )


class FakeCouponQuery(CouponQueryPort):
    def validate_coupon(self, coupon_code: str, order_subtotal: Decimal) -> Optional[CouponSnapshot]:
        if coupon_code == "INVALID":
            return None
        return CouponSnapshot(
            coupon_code=coupon_code,
            discount_amount=Decimal("50.00"),
            is_valid=True,
        )
