"""App-level composition root.

Lives OUTSIDE ``modules/`` on purpose: import-linter only constrains cross-app
imports inside ``modules`` (via ``application.ports``), so this is the only
place allowed to glue concrete adapters across bounded contexts.
"""

from functools import lru_cache

from modules.catalog.configuration.container import (
    CatalogContainer,
    get_catalog_container,
)
from modules.client.configuration.container import ClientContainer
from modules.order.configuration.container import OrderContainer
from modules.order.infrastructure.adapters.driven.catalog.catalog_product_query import (
    CatalogProductQuery,
)


@lru_cache(maxsize=1)
def get_app_catalog_container() -> CatalogContainer:
    """Exposes the catalog wiring root so its views stay out of modules.*."""
    return get_catalog_container()


@lru_cache(maxsize=1)
def get_app_client_container() -> ClientContainer:
    """Exposes the client wiring root so its views stay out of modules.*."""
    return ClientContainer()


@lru_cache(maxsize=1)
def get_app_container() -> OrderContainer:
    """Builds the order module wired to the real catalog query adapter."""
    catalog = get_catalog_container()
    catalog_query = CatalogProductQuery(catalog.product_query)
    return OrderContainer(catalog_query=catalog_query)
