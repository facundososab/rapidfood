from functools import lru_cache

from modules.catalog.application.use_cases.add_price_use_case import AddPriceUseCase
from modules.catalog.application.use_cases.create_category_use_case import (
    CreateCategoryUseCase,
)
from modules.catalog.application.use_cases.create_product_use_case import (
    CreateProductUseCase,
)
from modules.catalog.application.use_cases.get_product_use_case import (
    GetProductUseCase,
)
from modules.catalog.application.use_cases.list_categories_use_case import (
    ListCategoriesUseCase,
)
from modules.catalog.application.use_cases.update_product_use_case import (
    UpdateProductUseCase,
)
from modules.catalog.application.use_cases.product_query_use_case import (
    ProductQueryUseCase,
)
from modules.catalog.application.use_cases.list_prices_use_case import (
    ListPricesUseCase,
)
from modules.catalog.application.use_cases.list_products_use_case import (
    ListProductsUseCase,
)
from modules.catalog.application.use_cases.set_discount_use_case import (
    SetDiscountUseCase,
)
from modules.catalog.application.use_cases.set_product_state_use_case import (
    SetProductStateUseCase,
)
from modules.catalog.infrastructure.adapters.driven.prisma.category_repository import (
    PrismaCategoryRepository,
)
from modules.catalog.infrastructure.adapters.driven.prisma.discount_repository import (
    PrismaDiscountRepository,
)
from modules.catalog.infrastructure.adapters.driven.prisma.price_repository import (
    PrismaPriceRepository,
)
from modules.catalog.infrastructure.adapters.driven.prisma.product_repository import (
    PrismaProductRepository,
)
from shared.infrastructure.uuid_generator import UuidGenerator


class CatalogContainer:
    def __init__(self) -> None:
        products = PrismaProductRepository()
        prices = PrismaPriceRepository()
        categories = PrismaCategoryRepository()
        discounts = PrismaDiscountRepository()
        id_generator = UuidGenerator()

        self.create_product = CreateProductUseCase(products, categories, id_generator)
        self.set_product_state = SetProductStateUseCase(products)
        self.add_price = AddPriceUseCase(products, prices, id_generator)
        self.create_category = CreateCategoryUseCase(categories, id_generator)
        self.set_discount = SetDiscountUseCase(discounts, products, id_generator)
        self.product_query = ProductQueryUseCase(products, prices)
        self.list_products = ListProductsUseCase(products)
        self.list_prices = ListPricesUseCase(prices)
        self.list_categories = ListCategoriesUseCase(categories)
        self.get_product = GetProductUseCase(products, categories, prices)
        self.update_product = UpdateProductUseCase(products, categories, prices)

@lru_cache(maxsize=1)
def get_catalog_container() -> CatalogContainer:
    return CatalogContainer()