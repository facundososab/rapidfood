import hashlib
import hmac
from decimal import Decimal

import pytest

from modules.order.application.ports.driven.payment_provider import (
    CreateCheckoutLinkRequest,
)
from modules.order.domain.models.payment_status import PaymentStatus
from modules.order.infrastructure.adapters.driven.mercadopago.errors import (
    PaymentProviderError,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_payment_provider import (
    MercadoPagoPaymentProvider,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_settings import (
    MercadoPagoSettings,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_status_mapper import (
    map_mercadopago_status,
)
from modules.order.infrastructure.adapters.driver.rest.mercadopago_signature import (
    validate_mercadopago_signature,
)


class FakePreferenceResource:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.created_payloads = []

    def create(self, payload):
        self.created_payloads.append(payload)
        if self.error:
            raise self.error
        return self.result


class FakePaymentResource:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.requested_ids = []

    def get(self, payment_id):
        self.requested_ids.append(payment_id)
        if self.error:
            raise self.error
        return self.result


class FakeSDK:
    def __init__(self, preference_result=None, payment_result=None, preference_error=None):
        self.preference_resource = FakePreferenceResource(
            result=preference_result,
            error=preference_error,
        )
        self.payment_resource = FakePaymentResource(result=payment_result)

    def preference(self):
        return self.preference_resource

    def payment(self):
        return self.payment_resource


def make_settings(**overrides):
    values = {
        "access_token": "token",
        "notification_url": "https://api.example/webhook",
        "success_url": "https://front.example/success",
        "failure_url": "https://front.example/failure",
        "pending_url": "https://front.example/pending",
    }
    values.update(overrides)
    return MercadoPagoSettings(**values)


def test_maps_mercadopago_statuses_to_domain_statuses():
    assert map_mercadopago_status("approved") == PaymentStatus.APPROVED
    assert map_mercadopago_status("rejected") == PaymentStatus.REJECTED
    assert map_mercadopago_status("cancelled") == PaymentStatus.FAILED
    assert map_mercadopago_status("expired") == PaymentStatus.EXPIRED
    assert map_mercadopago_status("pending") == PaymentStatus.PENDING


def test_unknown_mercadopago_status_fails_closed():
    assert map_mercadopago_status("mystery") == PaymentStatus.FAILED


def test_settings_loads_env_and_defaults_to_ars(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "env-token")
    monkeypatch.setenv("MERCADOPAGO_NOTIFICATION_URL", "https://api.example/mp")
    monkeypatch.delenv("MERCADOPAGO_CURRENCY", raising=False)
    monkeypatch.delenv("MERCADOPAGO_WEBHOOK_SECRET", raising=False)

    settings = MercadoPagoSettings.from_env()

    assert settings.access_token == "env-token"
    assert settings.notification_url == "https://api.example/mp"
    assert settings.currency == "ARS"
    assert settings.webhook_secret is None
    assert settings.validate_webhook_signature is False


def test_settings_enables_signature_validation_when_secret_exists(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "env-token")
    monkeypatch.setenv("MERCADOPAGO_WEBHOOK_SECRET", "secret")

    settings = MercadoPagoSettings.from_env()

    assert settings.webhook_secret == "secret"
    assert settings.validate_webhook_signature is True


def test_create_checkout_link_sends_ars_preference_payload():
    sdk = FakeSDK(
        preference_result={
            "status": 201,
            "response": {
                "id": "pref-123",
                "init_point": "https://mp.example/checkout",
                "external_reference": "order-1",
            },
        }
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), sdk=sdk)

    result = provider.create_checkout_link(
        CreateCheckoutLinkRequest(
            order_id="order-1",
            payment_id="payment-1",
            amount=Decimal("1500.50"),
            currency="ARS",
            external_reference="order-1",
        )
    )

    assert result.preference_id == "pref-123"
    assert result.checkout_url == "https://mp.example/checkout"
    assert result.external_reference == "order-1"
    payload = sdk.preference_resource.created_payloads[0]
    assert payload["items"] == [
        {
            "title": "Rapidfood order order-1",
            "quantity": 1,
            "currency_id": "ARS",
            "unit_price": 1500.5,
        }
    ]
    assert payload["external_reference"] == "order-1"
    assert payload["notification_url"] == "https://api.example/webhook"


def test_get_payment_maps_sdk_response_to_provider_payment():
    sdk = FakeSDK(
        payment_result={
            "status": 200,
            "response": {
                "id": 987,
                "status": "approved",
                "external_reference": "order-1",
                "preference_id": "pref-123",
                "transaction_amount": 1500.5,
            },
        }
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), sdk=sdk)

    result = provider.get_payment("987")

    assert result.external_id == "987"
    assert result.status == PaymentStatus.APPROVED
    assert result.external_reference == "order-1"
    assert result.preference_id == "pref-123"
    assert result.amount == Decimal("1500.5")
    assert sdk.payment_resource.requested_ids == ["987"]


@pytest.mark.parametrize(
    "sdk_result",
    [
        {"status": 500, "response": {"message": "boom"}},
        {"status": 201, "response": {"id": "pref-123"}},
    ],
)
def test_provider_translates_sdk_failures_without_leaking_sdk_types(sdk_result):
    provider = MercadoPagoPaymentProvider(
        settings=make_settings(),
        sdk=FakeSDK(preference_result=sdk_result),
    )

    with pytest.raises(PaymentProviderError, match="Mercado Pago"):
        provider.create_checkout_link(
            CreateCheckoutLinkRequest(
                order_id="order-1",
                payment_id="payment-1",
                amount=Decimal("1500.00"),
                currency="ARS",
                external_reference="order-1",
            )
        )


def test_signature_validation_uses_mercadopago_hmac_manifest():
    secret = "webhook-secret"
    data_id = "ABC123"
    request_id = "req-1"
    ts = "1700000000"
    manifest = "id:abc123;request-id:req-1;ts:1700000000;"
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    assert validate_mercadopago_signature(
        data_id=data_id,
        x_request_id=request_id,
        x_signature=f"ts={ts},v1={digest}",
        secret=secret,
    )


def test_signature_validation_rejects_invalid_signature():
    assert not validate_mercadopago_signature(
        data_id="ABC123",
        x_request_id="req-1",
        x_signature="ts=1700000000,v1=invalid",
        secret="webhook-secret",
    )
