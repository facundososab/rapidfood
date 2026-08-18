"""URL routing — Rapidfood.

Route layout: ``/health`` plus per-app inbound adapters added by later changes.
"""

from django.urls import include, path

from config import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("catalog/", include("modules.catalog.infrastructure.adapters.driver.rest.urls")),
    path("api/orders/", include("modules.order.infrastructure.adapters.driver.rest.urls")),
]
