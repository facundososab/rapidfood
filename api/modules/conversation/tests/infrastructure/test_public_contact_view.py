"""Public contact REST endpoint: anonymous access, no-store cache, safe degrade.

Uses ``APIRequestFactory`` instead of ``django.test.Client`` on purpose: the
project urlconf eagerly builds the delivery container at import time, which
opens a Prisma connection. Calling the view directly keeps this a real unit
test with no URLconf, no database and no engine.
"""
from types import SimpleNamespace

from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from modules.conversation.application.ports.driver.public_contact_ports import (
    PublicContact,
)
from modules.conversation.infrastructure.adapters.driver.rest.views import (
    PublicContactView,
)


def _patch_container(monkeypatch, use_case):
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.get_app_conversation_container",
        lambda: SimpleNamespace(get_public_contact_use_case=use_case),
    )


def test_public_contact_view_is_anonymous_and_returns_contact(monkeypatch):
    _patch_container(
        monkeypatch,
        SimpleNamespace(
            execute=lambda bid: PublicContact(
                business_name="Pizzería Don Luigi",
                whatsapp_number="+5491112345678",
                whatsapp_enabled=True,
            )
        ),
    )
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.resolve_agent_business_config_id",
        lambda requested=None: "biz-1",
    )

    request = APIRequestFactory().get("/api/conversation/public-contact/")
    response = PublicContactView.as_view()(request)

    assert response.status_code == 200
    payload = response.data
    assert payload["business_name"] == "Pizzería Don Luigi"
    assert payload["whatsapp_number"] == "+5491112345678"
    assert payload["whatsapp_enabled"] is True
    assert response["Cache-Control"] == "no-store"


def test_public_contact_view_degrades_when_resolution_fails(monkeypatch):
    """No business configured / DB down must return an anonymous header, not a 500."""

    def boom(requested=None):
        raise RuntimeError("No business configuration found")

    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.resolve_agent_business_config_id",
        boom,
    )
    _patch_container(monkeypatch, SimpleNamespace(execute=lambda bid: None))

    request = APIRequestFactory().get("/api/conversation/public-contact/")
    response = PublicContactView.as_view()(request)

    assert response.status_code == 200
    assert response.data == {
        "business_name": None,
        "whatsapp_number": None,
        "whatsapp_enabled": False,
    }
    assert response["Cache-Control"] == "no-store"


def test_public_contact_view_degrades_when_the_use_case_fails(monkeypatch):
    _patch_container(
        monkeypatch,
        SimpleNamespace(execute=lambda bid: (_ for _ in ()).throw(RuntimeError("db down"))),
    )
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.rest.views.resolve_agent_business_config_id",
        lambda requested=None: "biz-1",
    )

    request = APIRequestFactory().get("/api/conversation/public-contact/")
    response = PublicContactView.as_view()(request)

    assert response.status_code == 200
    assert response.data["whatsapp_enabled"] is False


def test_public_contact_view_is_public_by_default():
    assert PublicContactView.permission_classes == [AllowAny]
    assert PublicContactView.authentication_classes == []
