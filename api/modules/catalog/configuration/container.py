from functools import lru_cache

from modules.catalog.application.use_cases.add_price_use_case import AddPriceUseCase
from modules.catalog.application.use_cases.create_category_use_case import (
    CreateCategoryUseCase,
)
from modules.catalog.application.use_cases.create_product_use_case import (
    CreateProductUseCase,
)
from modules.catalog.application.use_cases.delete_product_use_case import (
    DeleteProductUseCase,
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



from modules.catalog.infrastructure.adapters.driven.prisma.variant_repository import PrismaVariantRepository
from modules.catalog.infrastructure.adapters.driven.prisma.ingredient_repository import PrismaIngredientRepository
from modules.catalog.infrastructure.adapters.driven.prisma.variant_ingredient_repository import PrismaVariantIngredientRepository
from modules.catalog.infrastructure.adapters.driven.prisma.modifier_repository import PrismaModifierRepository

from modules.catalog.application.use_cases.create_variant_use_case import CreateVariantUseCase
from modules.catalog.application.use_cases.update_variant_use_case import UpdateVariantUseCase
from modules.catalog.application.use_cases.set_variant_price_use_case import SetVariantPriceUseCase
from modules.catalog.application.use_cases.create_ingredient_use_case import CreateIngredientUseCase
from modules.catalog.application.use_cases.update_ingredient_use_case import UpdateIngredientUseCase
from modules.catalog.application.use_cases.list_ingredients_use_case import ListIngredientsUseCase
from modules.catalog.application.use_cases.set_variant_ingredients_use_case import SetVariantIngredientsUseCase
from modules.catalog.application.use_cases.create_modifier_group_use_case import CreateModifierGroupUseCase
from modules.catalog.application.use_cases.update_modifier_group_use_case import UpdateModifierGroupUseCase
from modules.catalog.application.use_cases.create_modifier_option_use_case import CreateModifierOptionUseCase
from modules.catalog.application.use_cases.update_modifier_option_use_case import UpdateModifierOptionUseCase

class CatalogContainer:
    def __init__(self) -> None:
        products = PrismaProductRepository()
        prices = PrismaPriceRepository()
        categories = PrismaCategoryRepository()
        discounts = PrismaDiscountRepository()
        id_generator = UuidGenerator()
        variants = PrismaVariantRepository()

        self.create_product = CreateProductUseCase(product_repo=products, category_repo=categories, id_generator=id_generator, variant_repo=variants)
        self.delete_product = DeleteProductUseCase(products)
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