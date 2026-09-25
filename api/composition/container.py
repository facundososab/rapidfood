"""App-level composition root.

Lives OUTSIDE ``modules/`` on purpose: import-linter only constrains cross-app
imports inside ``modules`` (via ``application.ports``), so this is the only
place allowed to glue concrete adapters across bounded contexts.
"""

from functools import lru_cache

from modules.business.configuration.container import (
    BusinessContainer,
    get_business_container,
)
from modules.catalog.configuration.container import (
    CatalogContainer,
    get_catalog_container,
)
from modules.client.configuration.container import ClientContainer
from modules.config_coupon.configuration.container import CouponContainer, get_coupon_container
from modules.conversation.configuration.container import (
    ConversationContainer,
    build_container,
)
from modules.delivery.configuration.container import DeliveryContainer, get_delivery_container
from modules.mercadopago.configuration.container import (
    MercadoPagoContainer,
    get_mercadopago_container,
)
from modules.order.configuration.container import OrderContainer
from modules.order.infrastructure.adapters.driven.business.business_config_query_adapter import (
    BusinessConfigQueryAdapter,
)
from modules.order.infrastructure.adapters.driven.catalog.catalog_product_query import (
    CatalogProductQuery,
)
from modules.order.infrastructure.adapters.driven.client.client_query_adapter import (
    ClientQueryAdapter,
)
from modules.order.infrastructure.adapters.driven.coupon.coupon_consume_adapter import (
    CouponConsumeAdapter,
)
from modules.order.infrastructure.adapters.driven.coupon.coupon_query_adapter import (
    CouponQueryAdapter,
)
from modules.order.infrastructure.adapters.driven.delivery.delivery_quote_adapter import (
    DeliveryQuoteAdapter,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_credentials_query_adapter import (
    MercadoPagoCredentialsQueryAdapter,
)
from modules.staff.configuration.container import get_staff_container


@lru_cache(maxsize=1)
def get_app_catalog_container() -> CatalogContainer:
    """Exposes the catalog wiring root so its views stay out of modules.*."""
    return get_catalog_container()


@lru_cache(maxsize=1)
def get_app_client_container() -> ClientContainer:
    """Exposes the client wiring root so its views stay out of modules.*."""
    return ClientContainer()


@lru_cache(maxsize=1)
def get_app_business_container() -> BusinessContainer:
    return get_business_container()


@lru_cache(maxsize=1)
def get_app_staff_container() -> "StaffContainer":
    """Exposes the staff wiring root so its views stay out of modules.*."""
    return get_staff_container()


@lru_cache(maxsize=1)
def get_app_coupon_container() -> CouponContainer:
    return get_coupon_container()


@lru_cache(maxsize=1)
def get_app_conversation_container() -> ConversationContainer:
    return build_container()


@lru_cache(maxsize=1)
def get_app_delivery_container() -> DeliveryContainer:
    return get_delivery_container()


@lru_cache(maxsize=1)
def get_app_mercadopago_container() -> MercadoPagoContainer:
    """Exposes the Mercado Pago wiring root so its views stay out of modules.*."""
    return get_mercadopago_container()


@lru_cache(maxsize=1)
def get_app_container() -> OrderContainer:
    """Builds the order module wired to the real cross-context adapters."""
    catalog = get_catalog_container()
    client = get_app_client_container()
    business = get_app_business_container()
    coupon = get_app_coupon_container()
    delivery = get_app_delivery_container()
    mercadopago = get_app_mercadopago_container()

    return OrderContainer(
        catalog_query=CatalogProductQuery(catalog.product_query),
        client_query=ClientQueryAdapter(client.client_query_adapter),
        config_query=BusinessConfigQueryAdapter(business.get_configuration),
        coupon_query=CouponQueryAdapter(coupon.validate_coupon),
        coupon_consume=CouponConsumeAdapter(coupon.consume_coupon),
        delivery_quote=DeliveryQuoteAdapter(delivery.calculate_delivery_quote),
        credentials_query=MercadoPagoCredentialsQueryAdapter(
            mercadopago.get_access_token
        ),
    )
