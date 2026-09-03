from dataclasses import dataclass
from typing import Protocol

from modules.catalog.application.ports.driver.add_price_ports import AddPriceResponse


@dataclass(frozen=True)
class ListPricesQuery:
    product_id: str


class ListPricesPort(Protocol):
    def execute(self, query: ListPricesQuery) -> list[AddPriceResponse]: ...