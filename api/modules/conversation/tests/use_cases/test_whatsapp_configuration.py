import pytest

from modules.conversation.application.ports.driver.whatsapp_config_ports import (
    GetWhatsAppConfigurationQuery,
    SaveWhatsAppConfigurationCommand,
)
from modules.conversation.application.use_cases.get_whatsapp_configuration import (
    GetWhatsAppConfigurationUseCase,
)
from modules.conversation.application.use_cases.save_whatsapp_configuration import (
    SaveWhatsAppConfigurationUseCase,
)
from modules.conversation.domain.errors import (
    WhatsAppConfigurationNotFoundError,
    WhatsAppConfigurationValidationError,
)
from modules.conversation.tests.fakes import InMemoryWhatsAppConfigurationRepository


@pytest.fixture
def repo():
    return InMemoryWhatsAppConfigurationRepository()


def _save(repo, **overrides):
    command = {
        "business_config_id": "biz-1",
        "phone_number_id": "123456",
        "verify_token": "verify-me",
        "access_token": "token-abc",
        "app_secret": "secret-xyz",
    }
    command.update(overrides)
    return SaveWhatsAppConfigurationUseCase(repo).execute(
        SaveWhatsAppConfigurationCommand(**command)
    )


def test_save_then_get_masks_secrets(repo):
    _save(repo)
    view = GetWhatsAppConfigurationUseCase(repo).execute(
        GetWhatsAppConfigurationQuery(business_config_id="biz-1")
    )
    assert view.phone_number_id == "123456"
    assert view.verify_token == "verify-me"
    assert view.has_access_token is True
    assert view.has_app_secret is True
    assert not hasattr(view, "access_token")


def test_get_unknown_business_raises(repo):
    with pytest.raises(WhatsAppConfigurationNotFoundError):
        GetWhatsAppConfigurationUseCase(repo).execute(
            GetWhatsAppConfigurationQuery(business_config_id="missing")
        )


def test_first_save_requires_secrets(repo):
    with pytest.raises(WhatsAppConfigurationValidationError):
        _save(repo, access_token="", app_secret="")


def test_update_without_secrets_keeps_stored_values(repo):
    _save(repo)
    SaveWhatsAppConfigurationUseCase(repo).execute(
        SaveWhatsAppConfigurationCommand(
            business_config_id="biz-1",
            phone_number_id="123456",
            verify_token="verify-me",
            order_paid_template_name="order_paid",
        )
    )
    stored = repo.get_by_business_config_id("biz-1")
    assert stored.access_token == "token-abc"
    assert stored.app_secret == "secret-xyz"
    assert stored.order_paid_template_name == "order_paid"
