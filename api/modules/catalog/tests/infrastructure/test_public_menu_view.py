"""Public menu REST endpoint: anonymous access and no-store cache control.

Uses ``APIRequestFactory`` instead of ``django.test.Client`` on purpose: the
project urlconf eagerly builds the delivery container at import time, which
opens a Prisma connection (``DeliveryConfigurationRepository(db.client)``).
Calling the view directly keeps this a real unit test with no URLconf, no
database and no engine.
"""
from types import SimpleNamespace

from rest_framework.test import APIRequestFactory

from modules.catalog.application.ports.driver.get_public_menu_ports import (
    PublicCategory,
    PublicMenu,
    PublicProduct,
)
from modules.catalog.infrastructure.adapters.driver.rest.views import PublicMenuView


def _menu():
    return PublicMenu(
        categories=(
            PublicCategory(
                id="cat-1",
                name="Bebidas",
                products=(
                    PublicProduct(
                        id="p-1",
                        name="Coca",
                        description="Gaseosa",
                        image_url=None,
                    ),
                ),
            ),
        ),
    )


def test_public_menu_view_is_anonymous_and_returns_menu(monkeypatch):
    monkeypatch.setattr(
        "modules.catalog.infrastructure.adapters.driver.rest.views.get_app_catalog_container",
        lambda: SimpleNamespace(
            get_public_menu=SimpleNamespace(execute=lambda: _menu())
        ),
    )

    request = APIRequestFactory().get("/api/catalog/menu/")
    response = PublicMenuView.as_view()(request)

    assert response.status_code == 200
    payload = response.data
    assert payload["categories"][0]["id"] == "cat-1"
    assert payload["categories"][0]["name"] == "Bebidas"
    assert payload["categories"][0]["products"][0]["id"] == "p-1"
    assert payload["categories"][0]["products"][0]["name"] == "Coca"
    assert response["Cache-Control"] == "no-store"
