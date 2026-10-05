"""Order state-transition buttons and the kitchen board.

Covers the PR that replaced the free status select with valid-transition
buttons (``panel.domain.orders.valid_transitions``) and added ``/cocina/``.

Run with the UI settings: DJANGO_SETTINGS_MODULE=config.settings
"""
import base64
import json
from datetime import datetime
from decimal import Decimal

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from panel.domain import orders as orders_domain
from panel.services import dtos
from panel.services.client import Page


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _jwt_with_exp(exp: int) -> str:
    header = _b64url(b'{"alg":"none","typ":"JWT"}')
    payload = _b64url(json.dumps({"exp": exp}).encode("utf-8"))
    return f"{header}.{payload}.signature"


ACCESS_TOKEN = _jwt_with_exp(9999999999)


def _order(order_id="ord-1", status="CONFIRMED", payment_type=None,
           delivery_type="DELIVERY"):
    return dtos.Order(
        id=order_id,
        status=status,
        subtotal=Decimal("10"),
        discount=Decimal("0"),
        createdAt=datetime(2026, 1, 1, 12, 0, 0),
        paymentType=payment_type,
        deliveryType=delivery_type,
    )


def _targets(order):
    return [status for status, _label in orders_domain.valid_transitions(order)]


# --- valid_transitions -------------------------------------------------------

def test_draft_only_offers_pending():
    assert _targets(_order(status="DRAFT")) == ["PENDING"]


def test_pending_online_only_offers_paid():
    assert _targets(_order(status="PENDING", payment_type="ONLINE")) == ["PAID"]


def test_pending_cash_only_offers_confirmed():
    assert _targets(_order(status="PENDING", payment_type="CASH")) == ["CONFIRMED"]


def test_pending_without_payment_type_offers_both_settlements():
    assert _targets(_order(status="PENDING", payment_type=None)) == [
        "PAID",
        "CONFIRMED",
    ]


def test_paid_offers_confirmed():
    assert _targets(_order(status="PAID")) == ["CONFIRMED"]


def test_confirmed_offers_in_preparation():
    assert _targets(_order(status="CONFIRMED")) == ["IN_PREPARATION"]


def test_in_preparation_offers_ready():
    assert _targets(_order(status="IN_PREPARATION")) == ["READY"]


def test_ready_delivery_offers_delivered():
    assert _targets(_order(status="READY", delivery_type="DELIVERY")) == ["DELIVERED"]


def test_ready_pickup_offers_picked_up():
    assert _targets(_order(status="READY", delivery_type="PICKUP")) == ["PICKED_UP"]


@pytest.mark.parametrize("status", ["DELIVERED", "PICKED_UP", "CANCELLED"])
def test_terminal_states_offer_nothing(status):
    assert orders_domain.valid_transitions(_order(status=status)) == []


def test_every_offered_transition_is_reachable_from_the_backend_machine():
    """Guard against drift from the documented state machine.

    The UI re-declares the rules (see docs/order-state-machine.md), so pin the
    reachable targets the backend also allows.
    """
    expected = {
        ("DRAFT", None): {"PENDING"},
        ("PENDING", "ONLINE"): {"PAID"},
        ("PENDING", "CASH"): {"CONFIRMED"},
        ("PENDING", None): {"PAID", "CONFIRMED"},
        ("PAID", None): {"CONFIRMED"},
        ("CONFIRMED", None): {"IN_PREPARATION"},
        ("IN_PREPARATION", None): {"READY"},
    }
    for (status, payment_type), targets in expected.items():
        assert set(_targets(_order(status=status, payment_type=payment_type))) == targets


# --- kitchen board -----------------------------------------------------------

class _FakeClient:
    def __init__(self, orders):
        self._orders = orders
        self.updated = []

    def list_orders(self, *, page=1, page_size=15, **kwargs):
        return Page(items=self._orders, total=len(self._orders),
                    page=page, page_size=page_size)

    def update_order_status(self, order_id, status):
        self.updated.append((order_id, status))
        return next(o for o in self._orders if o.id == order_id)


@pytest.fixture()
def logged_in_client():
    client = Client()
    session = client.session
    session["supabase_access_token"] = ACCESS_TOKEN
    session["supabase_email"] = "admin@rapidfood.local"
    session.save()
    # Signed-cookie sessions are written as a cookie only on a response, so push
    # the freshly signed value onto the client's cookie jar before the request.
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client


def test_kitchen_board_lists_confirmed_and_in_preparation(
    logged_in_client, monkeypatch
):
    from panel.views import kitchen as kitchen_views

    confirmed = _order("ord-confirmed", status="CONFIRMED")
    preparing = _order("ord-preparing", status="IN_PREPARATION")
    delivered = _order("ord-delivered", status="DELIVERED")
    fake = _FakeClient([confirmed, preparing, delivered])
    monkeypatch.setattr(kitchen_views, "get_client", lambda: fake)

    response = logged_in_client.get(reverse("kitchen"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Cocina" in content
    assert confirmed.id in content
    assert preparing.id in content
    assert delivered.id not in content


def test_kitchen_board_renders_only_valid_transitions(
    logged_in_client, monkeypatch
):
    from panel.views import kitchen as kitchen_views

    confirmed = _order("ord-confirmed", status="CONFIRMED")
    preparing = _order("ord-preparing", status="IN_PREPARATION")
    fake = _FakeClient([confirmed, preparing])
    monkeypatch.setattr(kitchen_views, "get_client", lambda: fake)

    response = logged_in_client.get(reverse("kitchen"))
    content = response.content.decode()

    assert 'value="IN_PREPARATION"' in content
    assert 'value="READY"' in content
    assert 'value="DELIVERED"' not in content


# --- change_status redirect --------------------------------------------------

def test_change_status_redirects_back_to_referer(logged_in_client, monkeypatch):
    from panel.views import orders as orders_views

    fake = _FakeClient([_order("ord-1", status="CONFIRMED")])
    monkeypatch.setattr(orders_views, "get_client", lambda: fake)

    response = logged_in_client.post(
        reverse("order_change_status", args=["ord-1"]),
        {"status": "IN_PREPARATION"},
        HTTP_REFERER="/cocina/",
    )

    assert response.status_code == 302
    assert response.url == "/cocina/"
    assert fake.updated == [("ord-1", "IN_PREPARATION")]


def test_change_status_falls_back_to_order_detail_without_referer(
    logged_in_client, monkeypatch
):
    from panel.views import orders as orders_views

    fake = _FakeClient([_order("ord-1", status="CONFIRMED")])
    monkeypatch.setattr(orders_views, "get_client", lambda: fake)

    response = logged_in_client.post(
        reverse("order_change_status", args=["ord-1"]),
        {"status": "IN_PREPARATION"},
    )

    assert response.status_code == 302
    assert response.url == reverse("order_detail", args=["ord-1"])


def test_change_status_rejects_non_post(logged_in_client):
    response = logged_in_client.get(
        reverse("order_change_status", args=["ord-1"])
    )
    assert response.status_code == 400
