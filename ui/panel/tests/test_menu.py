"""Public menu page ("carta digital") tests.

Run with the UI settings: DJANGO_SETTINGS_MODULE=config.settings
"""
from django.test import Client
from django.urls import reverse

from panel.services.public_menu import (
    PublicCategory,
    PublicContact,
    PublicMenu,
    PublicModifierGroup,
    PublicModifierOption,
    PublicProduct,
    PublicVariant,
)

SAMPLE_CONTACT = PublicContact(
    business_name="La Hamburguesería",
    whatsapp_number="+54 9 11 1234-5678",
    whatsapp_enabled=True,
)


def _menu() -> PublicMenu:
    """One category, one product, one variant, one modifier group."""
    return PublicMenu(
        categories=(
            PublicCategory(
                id="c1",
                name="Burgers",
                products=(
                    PublicProduct(
                        id="p1",
                        name="Hamburguesa Clásica",
                        description="Con cheddar y lechuga",
                        image_url=None,
                        variants=(
                            PublicVariant(
                                id="v1", name="Simple", price="5200.00", available=True
                            ),
                        ),
                        modifier_groups=(
                            PublicModifierGroup(
                                id="g1",
                                name="Extras",
                                options=(
                                    PublicModifierOption(
                                        id="o1",
                                        name="Bacon",
                                        price_delta="800.00",
                                        available=True,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )


def _patch(monkeypatch, menu, contact):
    from panel.views import menu as menu_views

    monkeypatch.setattr(menu_views, "get_public_menu", lambda: menu)
    monkeypatch.setattr(menu_views, "get_public_contact", lambda: contact)


def test_menu_url_reverses_to_carta():
    assert reverse("menu") == "/carta/"


def test_carta_public_page_renders(monkeypatch):
    _patch(monkeypatch, _menu(), SAMPLE_CONTACT)

    response = Client().get("/carta/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "La Hamburguesería" in content  # business name becomes the title
    assert "Hamburguesa Clásica" in content  # product name
    assert "5.200" in content  # formatted variant price
    assert "https://wa.me/5491112345678" in content  # WhatsApp CTA url


def test_carta_empty_menu_still_renders(monkeypatch):
    _patch(monkeypatch, PublicMenu(categories=()), SAMPLE_CONTACT)

    response = Client().get("/carta/")

    assert response.status_code == 200
    assert "No pudimos cargar la carta" in response.content.decode("utf-8")


def test_carta_unavailable_variant_shows_marker(monkeypatch):
    menu = PublicMenu(
        categories=(
            PublicCategory(
                id="c1",
                name="Burgers",
                products=(
                    PublicProduct(
                        id="p1",
                        name="Hamburguesa",
                        description="",
                        image_url=None,
                        variants=(
                            PublicVariant(id="v1", name="Doble", price=None, available=False),
                        ),
                        modifier_groups=(),
                    ),
                ),
            ),
        )
    )
    _patch(monkeypatch, menu, SAMPLE_CONTACT)

    response = Client().get("/carta/")

    assert response.status_code == 200
    assert "No disponible" in response.content.decode("utf-8")
