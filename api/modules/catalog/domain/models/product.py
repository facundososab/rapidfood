from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ProductState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"

@dataclass #reemplaza al __init__
class Product:
    id: str
    name: str
    description: str
    state: ProductState
    category_id: str
    image_url: Optional[str] = None

    def mark_available(self) -> None:
        self.state = ProductState.AVAILABLE

    def mark_unavailable(self) -> None:
        self.state = ProductState.UNAVAILABLE
