from decimal import Decimal

from modules.catalog.application.ports.driver.product_query_ports import (
    ProductSnapshot as CatalogProductSnapshot,
)
from modules.order.infrastructure.adapters.driven.catalog.catalog_product_query import (
    CatalogProductQuery,
)


class FakeCatalogPort:
    def __init__(self, snapshot=None):
        self._snapshot = snapshot

    def find_product(self, product_id):
        return self._snapshot


def test_maps_catalog_snapshot_to_order_port():
    port = FakeCatalogPort(
        CatalogProductSnapshot(product_id="p-1", price=Decimal("150.00"), is_available=True)
    )
    adapter = CatalogProductQuery(port)

    snapshot = adapter.get_product("p-1")

    assert snapshot is not None
    assert snapshot.product_id == "p-1"
    assert snapshot.price == Decimal("150.00")
    assert snapshot.is_available is True


def test_returns_none_when_catalog_has_no_product():
    adapter = CatalogProductQuery(FakeCatalogPort(None))

    assert adapter.get_product("p-1") is None
