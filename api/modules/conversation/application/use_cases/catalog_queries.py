"""Catalog queries for the agent (menu browsing, product detail)."""
from __future__ import annotations

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driven.catalog_service import (
    CatalogServicePort,
    ProductDetailDTO,
    ProductSummaryDTO,
)
from modules.conversation.application.ports.driver.agent_commands import (
    GetProductDetailQuery,
    SearchProductsQuery,
)


class SearchProductsForConversationUseCase:
    def __init__(self, catalog: CatalogServicePort) -> None:
        self._catalog = catalog

    def execute(
        self, query: SearchProductsQuery, context: AgentExecutionContext
    ) -> list[ProductSummaryDTO]:
        # The business always comes from the trusted context, never the model.
        return self._catalog.search_products(
            context.business_configuration_id,
            query=query.query,
            category_id=query.category_id,
            only_available=query.only_available,
        )


class GetProductDetailForConversationUseCase:
    def __init__(self, catalog: CatalogServicePort) -> None:
        self._catalog = catalog

    def execute(
        self, query: GetProductDetailQuery, context: AgentExecutionContext
    ) -> ProductDetailDTO | None:
        return self._catalog.get_product_detail(
            context.business_configuration_id, query.product_id
        )
