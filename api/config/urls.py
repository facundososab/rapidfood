"""URL routing — Rapidfood."""

from django.urls import include, path

from config import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("api/conversation/", include("modules.conversation.infrastructure.adapters.driver.rest.urls")),
    path("api/catalog/", include("modules.catalog.infrastructure.adapters.driver.rest.urls")),
    path("api/clients/", include("modules.client.infrastructure.adapters.driver.rest.urls")),
    path("api/orders/", include("modules.order.infrastructure.adapters.driver.rest.urls")),
    path("api/coupons/", include("modules.config_coupon.infrastructure.adapters.driver.rest.urls")),
]
