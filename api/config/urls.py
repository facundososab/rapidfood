"""URL routing — Rapidfood."""

from django.urls import include, path

from api.config import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("conversation/", include("modules.conversation.infrastructure.adapters.driver.rest.urls")),
    path("catalog/", include("modules.catalog.infrastructure.adapters.driver.rest.urls")),
    path("api/orders/", include("modules.order.infrastructure.adapters.driver.rest.urls")),
]
