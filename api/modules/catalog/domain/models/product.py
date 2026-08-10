from dataclasses import dataclass
from enum import Enum

class ProductState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"

@dataclass #reemplaza al __init__
class Product:
    id: str
    description: str
    state: ProductState
    category_id: str

    def mark_available(self) -> None:
        self.state = ProductState.AVAILABLE

    def mark_unavailable(self) -> None:
        self.state = ProductState.UNAVAILABLE
