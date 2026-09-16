from decimal import Decimal

from modules.catalog.application.ports.driver.product_query_ports import (
    VariantContext as CatalogVariantContext,
)
from modules.order.infrastructure.adapters.driven.catalog.catalog_product_query import (
    CatalogProductQuery,
)


class FakeCatalogPort:
    def __init__(self, variant_context=None):
        self._variant_context = variant_context

    def find_product(self, product_id):
        return None

    def find_variant_context(self, variant_id):
        return self._variant_context


def test_maps_catalog_variant_context_to_order_port():
    catalog_ctx = CatalogVariantContext(
        product_id="p-1",
        product_name="Pizza",
        product_available=True,
        variant_id="v-1",
        variant_name="Regular",
        variant_available=True,
        current_price=Decimal("150.00"),
    )
    port = FakeCatalogPort(variant_context=catalog_ctx)
    adapter = CatalogProductQuery(port)

    ctx = adapter.get_variant_context("v-1")

    assert ctx is not None
    assert ctx.product_id == "p-1"
    assert ctx.variant_id == "v-1"
    assert ctx.current_price == Decimal("150.00")
    assert ctx.is_sellable is True


def test_returns_none_when_catalog_has_no_variant():
    adapter = CatalogProductQuery(FakeCatalogPort(None))

    assert adapter.get_variant_context("v-missing") is None
