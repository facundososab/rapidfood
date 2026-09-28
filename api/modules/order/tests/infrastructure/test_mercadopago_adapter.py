"""Mercado Pago Orders API adapter (HTTP transport injected, no credentials)."""
from decimal import Decimal

import pytest

from modules.order.application.ports.driven.payment_provider import (
    CancelCheckoutRequest,
    CreateCheckoutRequest,
    PaymentProviderError,
)
from modules.order.domain.models.payment_status import PaymentStatus
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_payment_provider import (
    MercadoPagoPaymentProvider,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_settings import (
    MercadoPagoSettings,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_status_mapper import (
    map_mercadopago_status,
)


class FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body if body is not None else {}

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses=None, error=None):
        self.responses = list(responses or [])
        self.error = error
        self.calls = []

    def request(self, method, url, headers=None, json=None, timeout=None):
        self.calls.append(
            {"method": method, "url": url, "headers": headers or {}, "json": json}
        )
        if self.error:
            raise self.error
        if self.responses:
            return self.responses.pop(0)
        return FakeResponse(200, {})


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


def make_request(**overrides):
    values = dict(
        order_id="order-1",
        attempt_id="attempt-1",
        amount=Decimal("1500.50"),
        currency="ARS",
        external_reference="order-1",
        idempotency_key="key-abc",
    )
    values.update(overrides)
    return CreateCheckoutRequest(**values)


def test_create_checkout_posts_to_orders_api_with_idempotency_key():
    session = FakeSession(
        [
            FakeResponse(
                201,
                {
                    "id": "MP-ORDER-1",
                    "status": "created",
                    "checkout_url": "https://mp.example/checkout",
                    "external_reference": "order-1",
                },
            )
        ]
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    result = provider.create_checkout(make_request())

    assert result.external_id == "MP-ORDER-1"
    assert result.checkout_url == "https://mp.example/checkout"
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/v1/orders")
    assert call["headers"]["X-Idempotency-Key"] == "key-abc"
    assert call["headers"]["Authorization"] == "Bearer token"
    assert call["json"]["total_amount"] == "1500.50"
    assert call["json"]["external_reference"] == "order-1"
    # Checkout Pro (Orders API) shape: manual processing, no transparent
    # `transactions` block, currency on the account (not on the item) and return
    # URLs under config.online.
    assert call["json"]["processing_mode"] == "manual"
    assert "transactions" not in call["json"]
    assert "notification_url" not in call["json"]
    assert "currency_id" not in call["json"]["items"][0]
    online = call["json"]["config"]["online"]
    assert online["success_url"] == "https://front.example/success"
    assert online["failure_url"] == "https://front.example/failure"
    assert online["pending_url"] == "https://front.example/pending"
    assert online["auto_return"] == "approved"


def test_retry_reuses_the_same_provider_key():
    session = FakeSession(
        [
            FakeResponse(201, {"id": "MP-1", "checkout_url": "https://mp/1"}),
            FakeResponse(201, {"id": "MP-1", "checkout_url": "https://mp/1"}),
        ]
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    provider.create_checkout(make_request())
    provider.create_checkout(make_request())

    keys = [call["headers"]["X-Idempotency-Key"] for call in session.calls]
    assert keys == ["key-abc", "key-abc"]


def test_create_checkout_rejects_incomplete_provider_response():
    session = FakeSession([FakeResponse(201, {"id": "MP-1"})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    with pytest.raises(PaymentProviderError):
        provider.create_checkout(make_request())


def test_provider_error_is_logged_with_status_and_body_without_secrets(caplog):
    import logging

    session = FakeSession(
        [
            FakeResponse(
                400,
                {
                    "errors": [
                        {
                            "code": "required_properties",
                            "message": "Missing properties",
                            "details": ["'$.items[0]' - invalid"],
                        }
                    ]
                },
            )
        ]
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(PaymentProviderError):
            provider.create_checkout(make_request())

    assert "status=400" in caplog.text
    assert "required_properties" in caplog.text
    # The Authorization header must never reach the logs.
    assert "Bearer token" not in caplog.text


def test_cancel_checkout_uses_its_own_key_and_reports_cancelled():
    session = FakeSession([FakeResponse(200, {"id": "MP-1", "status": "canceled"})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    result = provider.cancel_checkout(
        CancelCheckoutRequest(external_id="MP-1", idempotency_key="cancel-key")
    )

    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/v1/orders/MP-1/cancel")
    assert call["headers"]["X-Idempotency-Key"] == "cancel-key"
    assert result.already_cancelled is False


def test_cancel_checkout_reports_already_cancelled_idempotently():
    session = FakeSession([FakeResponse(409, {})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    result = provider.cancel_checkout(
        CancelCheckoutRequest(external_id="MP-1", idempotency_key="cancel-key")
    )

    assert result.already_cancelled is True


def test_get_payment_prefers_the_nested_transaction_status():
    session = FakeSession(
        [
            FakeResponse(
                200,
                {
                    "id": "MP-1",
                    "status": "processed",
                    "external_reference": "order-1",
                    "total_amount": "1500.50",
                    "transactions": {"payments": [{"status": "approved"}]},
                },
            )
        ]
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    result = provider.get_payment("MP-1")

    assert result.status == PaymentStatus.APPROVED
    assert result.external_reference == "order-1"
    assert result.amount == Decimal("1500.50")


def test_get_payment_returns_none_when_the_provider_does_not_know_the_order():
    session = FakeSession([FakeResponse(404, {"error": "not found"})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    assert provider.get_payment("UNKNOWN") is None


def test_get_payment_returns_none_for_an_invalid_order_id():
    # Mercado Pago answers 400 `invalid_path_param` for an unknown/simulated id.
    session = FakeSession(
        [FakeResponse(400, {"errors": [{"code": "invalid_path_param"}]})]
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    assert provider.get_payment("123456") is None


def test_get_payment_raises_on_a_transient_provider_failure():
    session = FakeSession([FakeResponse(500, {"error": "internal"})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    with pytest.raises(PaymentProviderError):
        provider.get_payment("MP-1")


def test_transport_errors_become_technical_provider_errors():
    session = FakeSession(error=RuntimeError("connection reset"))
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    with pytest.raises(PaymentProviderError):
        provider.get_payment("MP-1")


def test_non_2xx_responses_become_technical_provider_errors():
    session = FakeSession([FakeResponse(500, {"message": "boom"})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    with pytest.raises(PaymentProviderError):
        provider.get_payment("MP-1")


def test_maps_mercadopago_statuses_to_domain_statuses():
    assert map_mercadopago_status("approved") == PaymentStatus.APPROVED
    assert map_mercadopago_status("rejected") == PaymentStatus.REJECTED
    assert map_mercadopago_status("cancelled") == PaymentStatus.FAILED
    assert map_mercadopago_status("canceled") == PaymentStatus.FAILED
    assert map_mercadopago_status("expired") == PaymentStatus.EXPIRED
    assert map_mercadopago_status("pending") == PaymentStatus.PENDING
    assert map_mercadopago_status("created") == PaymentStatus.PENDING
    assert map_mercadopago_status("action_required") == PaymentStatus.PENDING


def test_orders_api_settled_payment_is_approved():
    """The Orders API settles a paid order as ``processed`` (detail ``accredited``).

    Mapping that to FAILED (fail-closed) used to leave every paid order in
    PENDING, so a confirmed webhook never marked the order as PAID.
    """
    assert map_mercadopago_status("processed") == PaymentStatus.APPROVED
    assert map_mercadopago_status("accredited") == PaymentStatus.APPROVED


def test_unknown_mercadopago_status_fails_closed():
    assert map_mercadopago_status("mystery") == PaymentStatus.FAILED


def test_settings_loads_env_and_orders_api_base(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "env-token")
    monkeypatch.delenv("MERCADOPAGO_CURRENCY", raising=False)
    monkeypatch.delenv("MERCADOPAGO_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("MERCADOPAGO_API_BASE_URL", raising=False)

    settings = MercadoPagoSettings.from_env()

    assert settings.access_token == "env-token"
    assert settings.currency == "ARS"
    assert settings.api_base_url == "https://api.mercadopago.com"
    assert settings.webhook_secret is None
    assert settings.validate_webhook_signature is False


def test_webhook_signature_validation_can_be_disabled_via_env(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "env-token")
    monkeypatch.setenv("MERCADOPAGO_WEBHOOK_SECRET", "s3cr3t")
    monkeypatch.setenv("MERCADOPAGO_VALIDATE_WEBHOOK_SIGNATURE", "false")

    settings = MercadoPagoSettings.from_env()

    assert settings.webhook_secret == "s3cr3t"
    assert settings.validate_webhook_signature is False


def test_create_checkout_uses_the_per_business_token_in_the_authorization_header():
    session = FakeSession(
        [FakeResponse(201, {"id": "MP-1", "checkout_url": "https://mp/1"})]
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    provider.create_checkout(make_request(access_token="APP_USR-business-token"))

    headers = session.calls[0]["headers"]
    assert headers["Authorization"] == "Bearer APP_USR-business-token"
    assert headers["X-Idempotency-Key"] == "key-abc"


def test_create_checkout_falls_back_to_the_configured_token_without_a_business_token():
    session = FakeSession(
        [FakeResponse(201, {"id": "MP-1", "checkout_url": "https://mp/1"})]
    )
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    provider.create_checkout(make_request())

    assert session.calls[0]["headers"]["Authorization"] == "Bearer token"


def test_get_payment_uses_the_per_business_token_in_the_authorization_header():
    session = FakeSession([FakeResponse(200, {"id": "MP-1", "status": "approved"})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    result = provider.get_payment("MP-1", access_token="APP_USR-business-token")

    assert result.status == PaymentStatus.APPROVED
    assert (
        session.calls[0]["headers"]["Authorization"]
        == "Bearer APP_USR-business-token"
    )


def test_get_payment_falls_back_to_the_configured_token_without_a_business_token():
    session = FakeSession([FakeResponse(200, {"id": "MP-1", "status": "approved"})])
    provider = MercadoPagoPaymentProvider(settings=make_settings(), session=session)

    provider.get_payment("MP-1")

    assert session.calls[0]["headers"]["Authorization"] == "Bearer token"


def test_signature_validation_uses_mercadopago_hmac_manifest():
    import hashlib
    import hmac

    from modules.order.infrastructure.adapters.driver.rest.mercadopago_signature import (
        validate_mercadopago_signature,
    )

    secret = "webhook-secret"
    data_id = "ABC123"
    request_id = "req-1"
    timestamp = "1700000000"
    manifest = "id:abc123;request-id:req-1;ts:1700000000;"
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    assert validate_mercadopago_signature(
        data_id=data_id,
        x_request_id=request_id,
        x_signature=f"ts={timestamp},v1={digest}",
        secret=secret,
    )


def test_signature_validation_rejects_invalid_signature():
    from modules.order.infrastructure.adapters.driver.rest.mercadopago_signature import (
        validate_mercadopago_signature,
    )

    assert not validate_mercadopago_signature(
        data_id="ABC123",
        x_request_id="req-1",
        x_signature="ts=1700000000,v1=invalid",
        secret="webhook-secret",
    )


def test_signature_validation_omits_id_when_absent_like_the_sdk():
    import hashlib
    import hmac

    from modules.order.infrastructure.adapters.driver.rest.mercadopago_signature import (
        validate_mercadopago_signature,
    )

    secret = "webhook-secret"
    manifest = "request-id:req-1;ts:1700000000;"
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    assert validate_mercadopago_signature(
        data_id="",
        x_request_id="req-1",
        x_signature=f"ts=1700000000,v1={digest}",
        secret=secret,
    )
