from dataclasses import dataclass
from typing import Optional, Protocol

from modules.catalog.application.ports.driver.get_product_ports import ProductDetail


@dataclass(frozen=True)
class UpdateProductCommand:
    product_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    available: Optional[bool] = None


class UpdateProductPort(Protocol):
    def execute(self, command: UpdateProductCommand) -> ProductDetail: ...