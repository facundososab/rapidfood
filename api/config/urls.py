"""URL routing — Rapidfood."""

from django.urls import include, path

from config import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("api/conversation/", include("modules.conversation.infrastructure.adapters.driver.rest.urls")),
    path("api/catalog/", include("modules.catalog.infrastructure.adapters.driver.rest.urls")),
    path("api/clients/", include("modules.client.infrastructure.adapters.driver.rest.urls")),
    path("api/orders/", include("modules.order.infrastructure.adapters.driver.rest.urls")),
    path("api/delivery/", include("modules.delivery.infrastructure.adapters.driver.rest.urls")),
    path("api/business/", include("modules.business.infrastructure.adapters.driver.rest.urls")),
]
