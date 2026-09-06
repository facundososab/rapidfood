from datetime import date
from typing import Protocol
from modules.catalog.domain.models.price import Price


class PriceRepositoryPort(Protocol):
    def add(self, price: Price) -> None: ...

    def list_for_product(self, product_variant_id: str) -> list[Price]: ...

    def find_current(self, product_variant_id: str, on_date: date) -> Price | None: ...
    