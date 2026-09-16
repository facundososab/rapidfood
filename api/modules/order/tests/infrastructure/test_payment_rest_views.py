import hashlib
import hmac

from django.urls import resolve
from rest_framework.test import APIRequestFactory

from modules.order.application.ports.driver.payment_ports import (
    CreatePaymentLinkResult,
    ProcessPaymentNotificationResult,
)
from modules.order.infrastructure.adapters.driver.rest.views import (
    MercadoPagoWebhookView,
    PaymentLinkView,
)


class FakeUseCase:
    def __init__(self, result):
        self.result = result
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return self.result


class FakeContainer:
    def __init__(self, webhook_secret=None):
        self.create_payment_link_use_case = FakeUseCase(
            CreatePaymentLinkResult(
                order_id="11111111-1111-1111-1111-111111111111",
                payment_id="payment-1",
                provider="MERCADOPAGO",
                checkout_url="https://pay.example/checkout",
                status="PENDING",
            )
        )
        self.process_payment_notification_use_case = FakeUseCase(
            ProcessPaymentNotificationResult(
                payment_id="payment-1",
                status="APPROVED",
                order_id="11111111-1111-1111-1111-111111111111",
                order_status="PAID",
                processed=True,
            )
        )
        self.mercadopago_settings = type(
            "MercadoPagoSettingsStub", (), {"webhook_secret": webhook_secret}
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


def test_payment_link_endpoint_delegates_to_use_case(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().post("/payment-link/", {}, format="json")

    response = PaymentLinkView.as_view()(
        request, order_id="11111111-1111-1111-1111-111111111111"
    )

    assert response.status_code == 201
    assert response.data == {
        "order_id": "11111111-1111-1111-1111-111111111111",
        "payment_id": "payment-1",
        "provider": "MERCADOPAGO",
        "checkout_url": "https://pay.example/checkout",
        "status": "PENDING",
    }
    assert len(container.create_payment_link_use_case.commands) == 1
    assert container.create_payment_link_use_case.commands[0].order_id == (
        "11111111-1111-1111-1111-111111111111"
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
    assert response.data == {"processed": True, "status": "APPROVED"}
    assert len(container.process_payment_notification_use_case.commands) == 1
    command = container.process_payment_notification_use_case.commands[0]
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
    assert container.process_payment_notification_use_case.commands == []


def test_order_payment_routes_are_registered():
    payment_link = resolve(
        "/11111111-1111-1111-1111-111111111111/payment-link/",
        urlconf="modules.order.infrastructure.adapters.driver.rest.urls",
    )
    webhook = resolve(
        "/payments/mercadopago/webhook/",
        urlconf="modules.order.infrastructure.adapters.driver.rest.urls",
    )

    assert payment_link.func.view_class is PaymentLinkView
    assert webhook.func.view_class is MercadoPagoWebhookView
