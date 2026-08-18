from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ProductSnapshot:
    product_id: str
    price: Decimal
    is_available: bool


class CatalogQuery(ABC):
    """
    Driven port to fetch product details from the catalog module.
    """
    
    @abstractmethod
    def get_product(self, product_id: str) -> Optional[ProductSnapshot]:
        """Fetches product details (price and availability)."""
        pass
