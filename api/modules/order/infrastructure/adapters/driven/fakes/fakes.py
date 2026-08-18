from modules.order.application.ports.driven.client_query import ClientQuery
from modules.order.application.ports.driven.catalog_query import CatalogQuery, ProductSnapshot
from modules.order.application.ports.driven.business_config_query import BusinessConfigQueryPort, BusinessConfigSnapshot
from modules.order.application.ports.driven.coupon_query import CouponQueryPort, CouponSnapshot
from typing import Optional
from decimal import Decimal


class FakeClientQuery(ClientQuery):
    def check_client_exists(self, client_id: str) -> bool:
        return True


class FakeCatalogQuery(CatalogQuery):
    def get_product(self, product_id: str) -> Optional[ProductSnapshot]:
        return ProductSnapshot(
            product_id=product_id,
            price=Decimal("150.00"),
            is_available=True
        )


class FakeBusinessConfigQuery(BusinessConfigQueryPort):
    def get_config(self) -> BusinessConfigSnapshot:
        return BusinessConfigSnapshot(
            is_open=True,
            shipping_cost=Decimal("50.00"),
            min_order_amount=Decimal("300.00")
        )


class FakeCouponQuery(CouponQueryPort):
    def validate_coupon(self, coupon_code: str, order_subtotal: Decimal) -> Optional[CouponSnapshot]:
        if coupon_code == "INVALID":
            return None
        return CouponSnapshot(
            coupon_code=coupon_code,
            discount_amount=Decimal("50.00"),
            is_valid=True
        )
