from decimal import Decimal
from typing import Any, Optional

from modules.order.application.ports.driven.payment_provider import (
    CreateCheckoutLinkRequest,
    CreateCheckoutLinkResult,
    PaymentProvider,
    ProviderPayment,
)
from modules.order.infrastructure.adapters.driven.mercadopago.errors import (
    PaymentProviderError,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_settings import (
    MercadoPagoSettings,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_status_mapper import (
    map_mercadopago_status,
)


class MercadoPagoPaymentProvider(PaymentProvider):
    def __init__(self, settings: MercadoPagoSettings, sdk: Optional[Any] = None):
        self.settings = settings
        if sdk is None:
            import mercadopago

            sdk = mercadopago.SDK(settings.access_token)
        self.sdk = sdk

    def create_checkout_link(
        self, request: CreateCheckoutLinkRequest
    ) -> CreateCheckoutLinkResult:
        payload = {
            "items": [
                {
                    "title": f"Rapidfood order {request.order_id}",
                    "quantity": 1,
                    "currency_id": request.currency or self.settings.currency,
                    "unit_price": float(request.amount),
                }
            ],
            "external_reference": request.external_reference,
        }
        if self.settings.notification_url:
            payload["notification_url"] = self.settings.notification_url
        back_urls = self._back_urls()
        if back_urls:
            payload["back_urls"] = back_urls

        result = self._call(lambda: self.sdk.preference().create(payload))
        response = self._successful_response(result, expected_status=201)
        preference_id = response.get("id")
        checkout_url = response.get("init_point")
        if not preference_id or not checkout_url:
            raise PaymentProviderError("Mercado Pago preference response is incomplete")
        return CreateCheckoutLinkResult(
            preference_id=str(preference_id),
            checkout_url=checkout_url,
            external_reference=response.get(
                "external_reference", request.external_reference
            ),
        )

    def get_payment(self, external_id: str) -> ProviderPayment:
        result = self._call(lambda: self.sdk.payment().get(external_id))
        response = self._successful_response(result, expected_status=200)
        return ProviderPayment(
            external_id=str(response["id"]),
            status=map_mercadopago_status(response.get("status", "")),
            external_reference=response.get("external_reference"),
            preference_id=response.get("preference_id"),
            amount=self._decimal_or_none(response.get("transaction_amount")),
        )

    def _back_urls(self) -> dict:
        urls = {}
        if self.settings.success_url:
            urls["success"] = self.settings.success_url
        if self.settings.failure_url:
            urls["failure"] = self.settings.failure_url
        if self.settings.pending_url:
            urls["pending"] = self.settings.pending_url
        return urls

    def _call(self, operation):
        try:
            return operation()
        except Exception as exc:
            raise PaymentProviderError("Mercado Pago request failed") from exc

    def _successful_response(self, result: dict, expected_status: int) -> dict:
        if result.get("status") != expected_status:
            raise PaymentProviderError("Mercado Pago request failed")
        response = result.get("response")
        if not isinstance(response, dict):
            raise PaymentProviderError("Mercado Pago response is invalid")
        return response

    def _decimal_or_none(self, value) -> Optional[Decimal]:
        return Decimal(str(value)) if value is not None else None
