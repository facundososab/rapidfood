from modules.catalog.application.ports.driver.add_price_ports import (
    AddPriceResponse,
)
from modules.catalog.application.ports.driver.list_prices_ports import (
    ListPricesPort,
    ListPricesQuery,
)
from modules.catalog.application.ports.driven.price_repository_port import (
    PriceRepositoryPort,
)


class ListPricesUseCase(ListPricesPort):
    def __init__(self, prices: PriceRepositoryPort) -> None:
        self._prices = prices

    def execute(self, query: ListPricesQuery) -> list[AddPriceResponse]:
        prices = self._prices.list_for_product(query.product_id)
        return [
            AddPriceResponse(id=p.id, product_id=p.product_id, since_date=p.since_date, price=p.price)
            for p in prices
        ]