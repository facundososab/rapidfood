from dataclasses import dataclass


@dataclass
class ProductVariant:
    id: str
    product_id: str
    name: str
    available: bool = True

    def mark_available(self) -> None:
        self.available = True

    def mark_unavailable(self) -> None:
        self.available = False
