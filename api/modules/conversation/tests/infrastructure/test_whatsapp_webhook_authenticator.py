import hashlib
import hmac

from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_webhook_authenticator import (
    WhatsAppWebhookAuthenticator,
)
from modules.conversation.tests.fakes import InMemoryWhatsAppConfigurationRepository

APP_SECRET = "app-secret"


def _repo(active=True):
    repo = InMemoryWhatsAppConfigurationRepository()
    repo.upsert(
        WhatsAppConfiguration(
            business_config_id="biz-1",
            phone_number_id="123456",
            verify_token="verify-me",
            access_token="t",
            app_secret=APP_SECRET,
            is_active=active,
        )
    )
    return repo


def _sign(raw: bytes, secret=APP_SECRET) -> str:
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_verify_subscription_matches_an_active_token():
    auth = WhatsAppWebhookAuthenticator(_repo())
    assert auth.verify_subscription("verify-me") is True
    assert auth.verify_subscription("nope") is False
    assert auth.verify_subscription("") is False


def test_resolve_identity_returns_a_safe_reference():
    identity = WhatsAppWebhookAuthenticator(_repo()).resolve_identity("123456")
    assert identity.business_config_id == "biz-1"
    assert identity.phone_number_id == "123456"
    assert not hasattr(identity, "app_secret")
    assert not hasattr(identity, "access_token")


def test_resolve_identity_is_none_for_unknown_or_inactive():
    auth = WhatsAppWebhookAuthenticator(_repo())
    assert auth.resolve_identity("999") is None
    assert WhatsAppWebhookAuthenticator(_repo(active=False)).resolve_identity("123456") is None


def test_verify_signature():
    auth = WhatsAppWebhookAuthenticator(_repo())
    raw = b'{"a": 1}'
    assert auth.verify_signature("123456", raw, _sign(raw)) is True
    assert auth.verify_signature("123456", raw, _sign(raw, "other")) is False
    assert auth.verify_signature("123456", raw, "") is False
    assert auth.verify_signature("999", raw, _sign(raw)) is False
