import hashlib
import hmac

from django.urls import resolve
from rest_framework.test import APIRequestFactory

from modules.order.application.ports.driver.payment_ports import (
    CancelSupersededCheckoutResult,
    CreatePaymentCheckoutResult,
    HandlePaymentWebhookResult,
)
from modules.order.infrastructure.adapters.driver.rest.views import (
    CancelSupersededCheckoutView,
    MercadoPagoWebhookView,
    PaymentLinkView,
)

ORDER_ID = "11111111-1111-1111-1111-111111111111"
ATTEMPT_ID = "22222222-2222-2222-2222-222222222222"


class FakeUseCase:
    def __init__(self, result):
        self.result = result
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return self.result


class FakeContainer:
    def __init__(self, webhook_secret=None, validate_signature=None):
        self.create_payment_checkout_use_case = FakeUseCase(
            CreatePaymentCheckoutResult(
                order_id=ORDER_ID,
                payment_attempt_id=ATTEMPT_ID,
                provider="MERCADOPAGO",
                checkout_url="https://pay.example/checkout",
                status="PENDING",
                order_version=5,
                created=True,
            )
        )
        self.handle_payment_webhook_use_case = FakeUseCase(
            HandlePaymentWebhookResult(
                payment_attempt_id=ATTEMPT_ID,
                status="APPROVED",
                order_id=ORDER_ID,
                order_status="PAID",
                processed=True,
                applied=True,
            )
        )
        self.cancel_superseded_checkout_use_case = FakeUseCase(
            CancelSupersededCheckoutResult(
                payment_attempt_id=ATTEMPT_ID,
                cancellation_status="CANCELLED",
                already_cancelled=False,
            )
        )
        validate = (
            bool(webhook_secret) if validate_signature is None else validate_signature
        )
        self.mercadopago_settings = type(
            "MercadoPagoSettingsStub",
            (),
            {
                "webhook_secret": webhook_secret,
                "validate_webhook_signature": validate,
            },
        )()


def patch_container(monkeypatch, container):
    monkeypatch.setattr(
        "modules.order.infrastructure.adapters.driver.rest.views.get_app_container",
        lambda: container,
    )


def sign(data_id, request_id, timestamp, secret):
    manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
    digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return f"ts={timestamp},v1={digest}"


def test_checkout_endpoint_delegates_to_use_case(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().post("/payment-link/", {}, format="json")

    response = PaymentLinkView.as_view()(request, order_id=ORDER_ID)

    assert response.status_code == 201
    assert response.data == {
        "order_id": ORDER_ID,
        "payment_attempt_id": ATTEMPT_ID,
        "provider": "MERCADOPAGO",
        "checkout_url": "https://pay.example/checkout",
        "status": "PENDING",
        "order_version": 5,
        "created": True,
    }
    assert len(container.create_payment_checkout_use_case.commands) == 1
    assert container.create_payment_checkout_use_case.commands[0].order_id == ORDER_ID


def test_cancel_checkout_endpoint_delegates(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().post("/cancel/", {}, format="json")

    response = CancelSupersededCheckoutView.as_view()(request, payment_attempt_id=ATTEMPT_ID)

    assert response.status_code == 200
    assert response.data == {
        "payment_attempt_id": ATTEMPT_ID,
        "cancellation_status": "CANCELLED",
        "already_cancelled": False,
    }
    assert (
        container.cancel_superseded_checkout_use_case.commands[0].payment_attempt_id
        == ATTEMPT_ID
    )


def test_webhook_endpoint_validates_signature_and_delegates(monkeypatch):
    container = FakeContainer(webhook_secret="secret")
    patch_container(monkeypatch, container)
    data_id = "mp-1"
    request_id = "request-1"

    request = APIRequestFactory().post(
        "/payments/mercadopago/webhook/",
        {"type": "payment", "data": {"id": data_id}, "status": "ignored"},
        format="json",
        HTTP_X_REQUEST_ID=request_id,
        HTTP_X_SIGNATURE=sign(data_id, request_id, "123", "secret"),
    )

    response = MercadoPagoWebhookView.as_view()(request)

    assert response.status_code == 200
    assert response.data == {
        "processed": True,
        "applied": True,
        "status": "APPROVED",
        "order_status": "PAID",
        "payment_attempt_id": ATTEMPT_ID,
    }
    assert len(container.handle_payment_webhook_use_case.commands) == 1
    command = container.handle_payment_webhook_use_case.commands[0]
    assert command.provider == "MERCADOPAGO"
    assert command.data_id == "mp-1"
    assert command.topic == "payment"
    assert command.raw_payload["status"] == "ignored"


def test_webhook_endpoint_rejects_invalid_signature_before_use_case(monkeypatch):
    container = FakeContainer(webhook_secret="secret")
    patch_container(monkeypatch, container)

    request = APIRequestFactory().post(
        "/payments/mercadopago/webhook/",
        {"type": "payment", "data": {"id": "mp-1"}},
        format="json",
        HTTP_X_REQUEST_ID="request-1",
        HTTP_X_SIGNATURE="ts=123,v1=bad",
    )

    response = MercadoPagoWebhookView.as_view()(request)

    assert response.status_code == 403
    assert container.handle_payment_webhook_use_case.commands == []


def test_webhook_skips_signature_when_validation_is_disabled(monkeypatch):
    """An explicit validate_webhook_signature=False bypasses the HMAC check."""
    container = FakeContainer(webhook_secret="secret", validate_signature=False)
    patch_container(monkeypatch, container)

    request = APIRequestFactory().post(
        "/payments/mercadopago/webhook/",
        {"type": "order", "data": {"id": "mp-1"}},
        format="json",
        HTTP_X_REQUEST_ID="request-1",
        HTTP_X_SIGNATURE="ts=123,v1=bad",
    )

    response = MercadoPagoWebhookView.as_view()(request)

    assert response.status_code == 200
    assert len(container.handle_payment_webhook_use_case.commands) == 1


def test_webhook_validates_signature_with_the_query_data_id(monkeypatch):
    """MP signs the manifest with ``data.id`` from the query string, not the body."""
    container = FakeContainer(webhook_secret="secret")
    patch_container(monkeypatch, container)
    data_id = "ORD01JYH1Z1YJN4HZ8J3Q0RB3YP6D"

    request = APIRequestFactory().post(
        "/payments/mercadopago/webhook/",
        {"type": "order"},
        format="json",
        QUERY_STRING=f"data.id={data_id}&type=order",
        HTTP_X_REQUEST_ID="request-1",
        HTTP_X_SIGNATURE=sign(data_id, "request-1", "123", "secret"),
    )

    response = MercadoPagoWebhookView.as_view()(request)

    assert response.status_code == 200
    assert container.handle_payment_webhook_use_case.commands[0].data_id == data_id


def test_webhook_requires_a_data_id(monkeypatch):
    container = FakeContainer(webhook_secret=None)
    patch_container(monkeypatch, container)

    request = APIRequestFactory().post(
        "/payments/mercadopago/webhook/", {"type": "order"}, format="json"
    )

    response = MercadoPagoWebhookView.as_view()(request)

    assert response.status_code == 400
    assert container.handle_payment_webhook_use_case.commands == []


def test_order_payment_routes_are_registered():
    payment_link = resolve(
        f"/{ORDER_ID}/payment-link/",
        urlconf="modules.order.infrastructure.adapters.driver.rest.urls",
    )
    cancel = resolve(
        f"/payments/attempts/{ATTEMPT_ID}/cancel/",
        urlconf="modules.order.infrastructure.adapters.driver.rest.urls",
    )
    webhook = resolve(
        "/payments/mercadopago/webhook/",
        urlconf="modules.order.infrastructure.adapters.driver.rest.urls",
    )

    assert payment_link.func.view_class is PaymentLinkView
    assert cancel.func.view_class is CancelSupersededCheckoutView
    assert webhook.func.view_class is MercadoPagoWebhookView
