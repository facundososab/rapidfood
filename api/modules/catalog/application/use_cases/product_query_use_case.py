from datetime import date
from decimal import Decimal
from typing import Optional

from modules.catalog.application.ports.driver.product_query_ports import (
    ProductQueryPort,
    ProductSnapshot,
)
from modules.catalog.application.ports.driven.price_repository_port import (
    PriceRepositoryPort,
)
from modules.catalog.application.ports.driven.product_repository_port import (
    ProductRepositoryPort,
)
from modules.catalog.domain.errors.catalog_errors import (
    ProductNotFoundError,
    ProductWithoutPriceError,
)
from modules.catalog.domain.models.product import ProductState


class ProductQueryUseCase(ProductQueryPort):
    def __init__(self, products: ProductRepositoryPort, prices: PriceRepositoryPort) -> None:
        self._products = products
        self._prices = prices

    def get_current_price(self, product_id: str) -> Decimal:
        if self._products.find_by_id(product_id) is None:
            raise ProductNotFoundError(product_id)

        price = self._prices.find_current(product_id, date.today())
        if price is None:
            raise ProductWithoutPriceError(product_id)

        return price.price

    def is_available(self, product_id: str) -> bool:
        product = self._products.find_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)

        return product.state == ProductState.AVAILABLE

    def find_product(self, product_id: str) -> Optional[ProductSnapshot]:
        product = self._products.find_by_id(product_id)
        if product is None:
            return None

        price = self._prices.find_current(product_id, date.today())
        if price is None:
            return None

        return ProductSnapshot(
            product_id=product_id,
            price=price.price,
            is_available=product.state == ProductState.AVAILABLE,
        )