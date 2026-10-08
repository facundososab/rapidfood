"""GetPublicContactUseCase: degrades safely and never exposes secrets."""
from __future__ import annotations

from modules.conversation.application.use_cases.get_public_contact import (
    GetPublicContactUseCase,
)
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)


class FakeWhatsAppConfigRepository:
    def __init__(self, config=None, exc=None):
        self._config = config
        self._exc = exc

    def get_by_business_config_id(self, business_config_id):
        if self._exc is not None:
            raise self._exc
        return self._config


class FakeBusinessService:
    def __init__(self, name=None, exc=None):
        self._name = name
        self._exc = exc

    def get_name(self, business_configuration_id):
        if self._exc is not None:
            raise self._exc
        return self._name


def _config(**overrides):
    defaults = dict(
        business_config_id="biz-1",
        phone_number_id="123456",
        verify_token="verify-me",
        access_token="token-abc",
        app_secret="secret-xyz",
        display_phone_number="+5491112345678",
        is_active=True,
    )
    defaults.update(overrides)
    return WhatsAppConfiguration(**defaults)


def test_config_present_active_returns_full_profile():
    repo = FakeWhatsAppConfigRepository(_config())
    business = FakeBusinessService("Pizzería Don Luigi")

    view = GetPublicContactUseCase(repo, business).execute("biz-1")

    assert view.business_name == "Pizzería Don Luigi"
    assert view.whatsapp_number == "+5491112345678"
    assert view.whatsapp_enabled is True


def test_config_absent_returns_name_only():
    repo = FakeWhatsAppConfigRepository(None)
    business = FakeBusinessService("Pizzería Don Luigi")

    view = GetPublicContactUseCase(repo, business).execute("biz-1")

    assert view.business_name == "Pizzería Don Luigi"
    assert view.whatsapp_number is None
    assert view.whatsapp_enabled is False


def test_repository_raises_degrades_without_crash():
    repo = FakeWhatsAppConfigRepository(exc=RuntimeError("db down"))
    business = FakeBusinessService("Pizzería Don Luigi")

    view = GetPublicContactUseCase(repo, business).execute("biz-1")

    assert view.business_name == "Pizzería Don Luigi"
    assert view.whatsapp_number is None
    assert view.whatsapp_enabled is False


def test_business_service_none_yields_no_name():
    repo = FakeWhatsAppConfigRepository(_config())

    view = GetPublicContactUseCase(repo, None).execute("biz-1")

    assert view.business_name is None
    assert view.whatsapp_number == "+5491112345678"
    assert view.whatsapp_enabled is True


def test_inactive_config_disables_whatsapp():
    repo = FakeWhatsAppConfigRepository(_config(is_active=False))

    view = GetPublicContactUseCase(repo, None).execute("biz-1")

    assert view.whatsapp_enabled is False
    assert view.whatsapp_number == "+5491112345678"
