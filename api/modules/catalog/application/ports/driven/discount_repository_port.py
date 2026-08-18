from typing import Protocol
from modules.catalog.domain.models.discount import Discount

class DiscountRepositoryPort(Protocol):
    def save(self, discount: Discount) -> None: ...

    def list_for_product(self, product_id: str) -> list[Discount]: ...
    