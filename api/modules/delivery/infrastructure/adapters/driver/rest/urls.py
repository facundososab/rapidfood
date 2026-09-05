"""URL routing for the delivery REST inbound adapter.

Follows the same pattern as config_coupon: use cases are injected at
URL-wiring time using APIView.as_view(use_case=container.use_case).

Endpoint design:
    GET  /api/delivery/{business_config_id}/configure/  — retrieve current config
    POST /api/delivery/{business_config_id}/configure/  — create/update config
    POST /api/delivery/{business_config_id}/quote/      — calculate quote
"""

from __future__ import annotations

from django.urls import path

from modules.delivery.configuration.container import get_delivery_container
from modules.delivery.infrastructure.adapters.driver.rest import views

_container = get_delivery_container()

_configure = views.DeliveryConfigurationView.as_view(
    get_delivery_configuration=_container.get_delivery_configuration,
    configure_delivery=_container.configure_delivery,
)
_quote = views.CalculateDeliveryQuoteView.as_view(
    calculate_delivery_quote=_container.calculate_delivery_quote,
)

urlpatterns = [
    path(
        "<str:business_config_id>/configure/",
        _configure,
        name="delivery-configuration",
    ),
    path(
        "<str:business_config_id>/quote/",
        _quote,
        name="delivery-quote",
    ),
]
