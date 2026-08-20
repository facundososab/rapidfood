from typing import Optional

from modules.catalog.application.ports.driver.product_query_ports import (
    ProductQueryPort,
)
from modules.order.application.ports.driven.catalog_query import (
    CatalogQuery,
    ProductSnapshot,
)


class CatalogProductQuery(CatalogQuery):
    """Adapts the catalog module's public query port to the order driven port.

    The order module depends only on ``modules.catalog.application.ports``
    (enforced by import-linter); the concrete query is injected by the
    composition root.
    """

    def __init__(self, catalog_query: ProductQueryPort) -> None:
        self._catalog_query = catalog_query

    def get_product(self, product_id: str) -> Optional[ProductSnapshot]:
        product = self._catalog_query.find_product(product_id)
        if product is None:
            return None

        return ProductSnapshot(
            product_id=product.product_id,
            price=product.price,
            is_available=product.is_available,
        )
