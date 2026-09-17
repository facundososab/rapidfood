"""Catalog queries for the conversation agent (fakes only)."""
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driven.catalog_service import (
    IngredientDTO,
    ModifierGroupDTO,
    ModifierOptionDTO,
    ProductDetailDTO,
    ProductSummaryDTO,
    VariantDTO,
)
from modules.conversation.application.ports.driver.agent_commands import (
    GetProductDetailQuery,
    SearchProductsQuery,
)
from modules.conversation.application.use_cases.catalog_queries import (
    GetProductDetailForConversationUseCase,
    SearchProductsForConversationUseCase,
)


class FakeCatalogService:
    def __init__(self):
        self.search_calls = []
        self.detail_calls = []

    def search_products(self, business_configuration_id, query=None, category_id=None, only_available=True):
        self.search_calls.append(
            {
                "business": business_configuration_id,
                "query": query,
                "category_id": category_id,
                "only_available": only_available,
            }
        )
        return [
            ProductSummaryDTO(
                id="p-1", name="Stacker", description="d", available=True, category_id="c-1"
            )
        ]

    def get_product_detail(self, business_configuration_id, product_id):
        self.detail_calls.append(
            {"business": business_configuration_id, "product_id": product_id}
        )
        return ProductDetailDTO(
            id=product_id,
            name="Stacker",
            description="d",
            available=True,
            variants=(
                VariantDTO(
                    id="v-1",
                    name="Doble",
                    current_price="1200",
                    available=True,
                    ingredients=(IngredientDTO("i-1", "Cebolla", True),),
                ),
            ),
            modifier_groups=(
                ModifierGroupDTO(
                    id="g-1",
                    name="Extras",
                    min_selections=0,
                    max_selections=3,
                    options=(ModifierOptionDTO("o-1", "Bacon", "200", True),),
                ),
            ),
        )


def _context(**overrides):
    values = dict(
        business_configuration_id="biz-1",
        conversation_id="conv-1",
        channel="LANGSMITH",
        client_id="client-1",
        external_thread_id="thread-1",
    )
    values.update(overrides)
    return AgentExecutionContext(**values)


def test_search_uses_the_context_business_not_the_model():
    catalog = FakeCatalogService()
    use_case = SearchProductsForConversationUseCase(catalog)

    result = use_case.execute(
        SearchProductsQuery(query="stacker", only_available=True),
        _context(business_configuration_id="biz-1"),
    )

    assert result[0].name == "Stacker"
    assert catalog.search_calls == [
        {
            "business": "biz-1",
            "query": "stacker",
            "category_id": None,
            "only_available": True,
        }
    ]


def test_search_ignores_a_business_supplied_by_the_caller():
    catalog = FakeCatalogService()
    use_case = SearchProductsForConversationUseCase(catalog)

    # The command has no business field at all: only the context can set it.
    use_case.execute(SearchProductsQuery(), _context(business_configuration_id="biz-9"))

    assert catalog.search_calls[0]["business"] == "biz-9"


def test_product_detail_includes_variants_ingredients_and_modifiers():
    catalog = FakeCatalogService()
    use_case = GetProductDetailForConversationUseCase(catalog)

    detail = use_case.execute(GetProductDetailQuery(product_id="p-1"), _context())

    assert detail.name == "Stacker"
    assert detail.variants[0].current_price == "1200"
    assert detail.variants[0].ingredients[0].removable is True
    assert detail.modifier_groups[0].options[0].price_delta == "200"
    assert catalog.detail_calls[0] == {"business": "biz-1", "product_id": "p-1"}


def test_execution_context_requires_identity():
    import pytest

    with pytest.raises(ValueError):
        _context(business_configuration_id="")
    with pytest.raises(ValueError):
        _context(conversation_id="")
