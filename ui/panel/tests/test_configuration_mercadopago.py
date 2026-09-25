"""Panel tests for the Mercado Pago linking section in configuration.

Run with the UI settings: DJANGO_SETTINGS_MODULE=config.settings
"""
import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from panel.services.mock_client import MockRapidfoodClient
from panel.views import configuration as configuration_views

PAYMENTS_URL = "/configuracion/pagos/"
LINK_URL = "/configuracion/pagos/vincular/"
UNLINK_URL = "/configuracion/pagos/desvincular/"


class StubClient(MockRapidfoodClient):
    """Mock client with configurable Mercado Pago responses (no network)."""

    def __init__(self, status=None, authorization_url=""):
        super().__init__()
        self._status = status if status is not None else {
            "linked": False,
            "live_mode": None,
            "user_id": None,
            "public_key": None,
        }
        self._authorization_url = authorization_url
        self.unlinked_ids = []

    def get_mercadopago_status(self):
        return self._status

    def get_mercadopago_authorization_url(self, business_config_id):
        return self._authorization_url

    def unlink_mercadopago(self, business_config_id):
        self.unlinked_ids.append(business_config_id)


def _authenticated_client(role):
    client = Client()
    session = client.session
    session["supabase_access_token"] = "test-token"
    session["supabase_email"] = "staff@rapidfood.local"
    session["supabase_staff"] = {
        "email": "staff@rapidfood.local",
        "name": "Staff Test",
        "role": role,
    }
    session.save()
    # Signed-cookie sessions are written as a cookie only on a response, so push
    # the freshly signed value onto the client's cookie jar before the request.
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client


@pytest.fixture()
def stub_client(monkeypatch):
    client = StubClient()
    monkeypatch.setattr(configuration_views, "get_client", lambda: client)
    return client


def test_admin_sees_payments_card_with_link_button(stub_client):
    response = _authenticated_client("ADMIN").get(PAYMENTS_URL)

    assert response.status_code == 200
    assert b"Mercado Pago" in response.content
    assert b"Vincular cuenta de Mercado Pago" in response.content


def test_non_admin_sees_payments_card_without_actions(stub_client):
    response = _authenticated_client("CASHIER").get(PAYMENTS_URL)

    assert response.status_code == 200
    assert b"Mercado Pago" in response.content
    assert b"Solo administradores" in response.content
    assert b"Vincular cuenta de Mercado Pago" not in response.content


def test_link_redirects_admin_to_the_authorization_url(monkeypatch):
    authorization_url = "https://auth.mercadopago.com/authorization?state=signed-state"
    client = StubClient(authorization_url=authorization_url)
    monkeypatch.setattr(configuration_views, "get_client", lambda: client)

    response = _authenticated_client("ADMIN").post(LINK_URL)

    assert response.status_code == 302
    assert response.url == authorization_url


def test_link_with_empty_url_reports_an_error_and_returns_to_payments(monkeypatch):
    client = StubClient(authorization_url="")
    monkeypatch.setattr(configuration_views, "get_client", lambda: client)

    response = _authenticated_client("ADMIN").post(LINK_URL, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[-1][0].endswith(reverse("configuration_payments_view"))
    assert "No se pudo iniciar la vinculación con Mercado Pago." in response.content.decode()


def test_link_rejects_non_post_requests(stub_client):
    response = _authenticated_client("ADMIN").get(LINK_URL)

    assert response.status_code == 400


def test_link_forbids_non_admin(stub_client):
    response = _authenticated_client("CASHIER").post(LINK_URL)

    assert response.status_code == 403


def test_unlink_redirects_and_unlinks_the_business(stub_client):
    response = _authenticated_client("ADMIN").post(UNLINK_URL)

    assert response.status_code == 302
    assert response.url == reverse("configuration_payments_view")
    assert stub_client.unlinked_ids == [stub_client.get_business_config().id]


def test_unlink_rejects_non_post_requests(stub_client):
    response = _authenticated_client("ADMIN").get(UNLINK_URL)

    assert response.status_code == 400


def test_unlink_forbids_non_admin(stub_client):
    response = _authenticated_client("CASHIER").post(UNLINK_URL)

    assert response.status_code == 403
