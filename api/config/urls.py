from django.urls import include, path

from config import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("catalog/", include("modules.catalog.infrastructure.adapters.driver.rest.urls")),
]