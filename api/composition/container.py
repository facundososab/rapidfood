"""App-level composition root.

Lives OUTSIDE ``modules/`` on purpose: import-linter only constrains cross-app
imports inside ``modules`` (via ``application.ports``), so this is the only
place allowed to glue concrete adapters across bounded contexts.
"""

import logging
from functools import lru_cache
from typing import Optional

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
from modules.conversation.infrastructure.adapters.driven.business_service_adapter import (
    BusinessServiceAdapter,
)
from modules.conversation.infrastructure.adapters.driven.catalog_service_adapter import (
    CatalogServiceAdapter,
)
from modules.conversation.infrastructure.adapters.driven.client_service_adapter import (
    ClientServiceAdapter,
)
from modules.conversation.infrastructure.adapters.driven.delivery_service_adapter import (
    DeliveryServiceAdapter,
)
from modules.conversation.infrastructure.adapters.driven.order_service_adapter import (
    OrderServiceAdapter,
)
from modules.delivery.configuration.container import DeliveryContainer, get_delivery_container
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

logger = logging.getLogger(__name__)


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
def get_app_coupon_container() -> CouponContainer:
    return get_coupon_container()


@lru_cache(maxsize=1)
def get_app_conversation_container() -> ConversationContainer:
    """Builds the conversation module wired to the real cross-context adapters."""
    catalog = get_catalog_container()
    order = get_app_container()
    delivery = get_app_delivery_container()

    catalog_service = CatalogServiceAdapter(
        list_products=catalog.list_products,
        product_query=catalog.product_query,
        get_product=catalog.get_product,
    )
    order_service = OrderServiceAdapter(
        get_current_order=order.get_current_order_use_case,
        get_latest_active_order=order.get_latest_active_order_use_case,
        get_order_summary=order.get_order_summary_use_case,
        get_or_create_current_draft=order.get_or_create_current_draft_use_case,
        add_item=order.add_item_to_order_use_case,
        update_item=order.update_item_in_order_use_case,
        remove_item=order.remove_item_from_order_use_case,
        set_delivery=order.set_delivery_for_order_use_case,
        set_pickup=order.set_pickup_for_order_use_case,
        set_payment_type=order.set_payment_type_use_case,
        set_client=order.set_client_for_order_use_case,
        apply_coupon=order.apply_coupon_to_order_use_case,
        confirm_order=order.confirm_order_use_case,
        cancel_order=order.cancel_order_use_case,
        create_payment_checkout=order.create_payment_checkout_use_case,
        cancel_superseded_checkout=order.cancel_superseded_checkout_use_case,
    )
    delivery_service = DeliveryServiceAdapter(delivery.calculate_delivery_quote)
    business_service = BusinessServiceAdapter(
        get_app_business_container().get_configuration
    )
    client = get_app_client_container()
    client_service = ClientServiceAdapter(
        client.client_query_adapter.find_by_phone_number, client.create_client
    )

    return build_container(
        catalog_service=catalog_service,
        order_service=order_service,
        delivery_service=delivery_service,
        business_service=business_service,
        client_service=client_service,
        agent_runner_factory=_build_agent_runner,
    )


def resolve_agent_business_config_id(requested: Optional[str] = None) -> str:
    """Resolve the business id for an agent turn, tolerant of re-seeds.

    The business row id is a generated UUID (re-seeding the database creates a
    NEW id), so a hardcoded id in the environment can go stale. Precedence:

      1. an explicit id from the channel/runtime context (multi-tenant correct);
      2. ``AGENT_BUSINESS_CONFIG_ID`` (dev convenience);
      3. the single existing business (what the business module calls "default").

    An explicit id is validated: a stale one falls back to the single business
    instead of being written as a foreign key that does not exist.
    """
    from django.conf import settings

    from modules.business.application.ports.driver.get_business_configuration_port import (
        GetBusinessConfigurationQuery,
    )

    business = get_app_business_container()
    candidate = (requested or "").strip() or (
        getattr(settings, "AGENT_BUSINESS_CONFIG_ID", "") or ""
    ).strip()

    if candidate and candidate != "default":
        try:
            return business.get_configuration.execute(
                GetBusinessConfigurationQuery(business_config_id=candidate)
            )["id"]
        except Exception:
            logger.warning(
                "Business configuration %r not found; falling back to the single "
                "configured business.",
                candidate,
            )

    try:
        return business.get_configuration.execute(
            GetBusinessConfigurationQuery(business_config_id="default")
        )["id"]
    except Exception as exc:
        raise RuntimeError(
            "No business configuration found. Create one (Configuración) or set "
            "AGENT_BUSINESS_CONFIG_ID."
        ) from exc


def _build_agent_runner(conversation_container):
    """Build the LangChain agent runner when a Groq key is configured.

    Returns None when the key is missing so the REST/app wiring still boots; the
    agent endpoint surfaces a clear error instead.

    LangSmith tracing is opt-in and read directly from the environment by the
    LangChain client (LANGSMITH_TRACING / LANGSMITH_API_KEY / LANGSMITH_PROJECT);
    it is not duplicated into Django settings. Secrets are never added to
    metadata.
    """
    from django.conf import settings

    from modules.conversation.infrastructure.adapters.driver.langchain.langchain_conversation_agent_adapter import (
        build_agent_runner,
    )

    api_key = getattr(settings, "GROQ_API_KEY", "")
    if not api_key:
        return None
    return build_agent_runner(
        conversation_container,
        model_name=getattr(settings, "AGENT_MODEL", "openai/gpt-oss-120b"),
        api_key=api_key,
    )


@lru_cache(maxsize=1)
def get_app_delivery_container() -> DeliveryContainer:
    return get_delivery_container()


@lru_cache(maxsize=1)
def get_app_container() -> OrderContainer:
    """Builds the order module wired to the real cross-context adapters."""
    catalog = get_catalog_container()
    client = get_app_client_container()
    business = get_app_business_container()
    coupon = get_app_coupon_container()
    delivery = get_app_delivery_container()

    return OrderContainer(
        catalog_query=CatalogProductQuery(catalog.product_query),
        client_query=ClientQueryAdapter(client.client_query_adapter),
        config_query=BusinessConfigQueryAdapter(business.get_configuration),
        coupon_query=CouponQueryAdapter(coupon.validate_coupon),
        coupon_consume=CouponConsumeAdapter(coupon.consume_coupon),
        delivery_quote=DeliveryQuoteAdapter(delivery.calculate_delivery_quote),
    )
