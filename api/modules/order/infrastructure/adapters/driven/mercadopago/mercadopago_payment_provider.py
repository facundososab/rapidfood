"""Mercado Pago Checkout Pro adapter using the Orders API.

``POST /v1/orders`` to create a checkout and ``POST /v1/orders/{id}/cancel`` to
cancel a superseded one. Both calls carry a stable ``X-Idempotency-Key`` supplied
by the application: a timeout retry reuses the same key so the provider does not
create a second logical checkout.

The HTTP transport is injected (``session``), so the adapter is unit-testable
without credentials. The exact Orders API payload/response fields depend on the
Mercado Pago account/version, so the response parsing is defensive and MUST be
validated against live credentials before production use.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

import requests

from modules.order.application.ports.driven.payment_provider import (
    CancelCheckoutRequest,
    CancelCheckoutResult,
    CreateCheckoutRequest,
    CreateCheckoutResult,
    PaymentProviderPort,
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

_ORDERS_PATH = "/v1/orders"

logger = logging.getLogger(__name__)


class MercadoPagoPaymentProvider(PaymentProviderPort):
    def __init__(self, settings: MercadoPagoSettings, session: Optional[Any] = None):
        self.settings = settings
        self._session = session if session is not None else requests.Session()

    def create_checkout(self, request: CreateCheckoutRequest) -> CreateCheckoutResult:
        amount = _amount_str(request.amount)
        # Checkout Pro (Orders API) payload. Differences from the Checkout API
        # (transparent) flow that MUST be respected:
        #   - processing_mode is always "manual" for Checkout Pro;
        #   - no `transactions` block (that is the transparent flow; sending it
        #     without `payment_method` is rejected);
        #   - `currency_id` lives on the account, not on the item;
        #   - return URLs go under `config.online` (there is no root
        #     `notification_url`; notifications are configured in the panel).
        payload: dict[str, Any] = {
            "type": "online",
            "processing_mode": "manual",
            "external_reference": request.external_reference,
            "total_amount": amount,
            "items": [
                {
                    "title": request.description
                    or f"Rapidfood order {request.order_id}",
                    "quantity": 1,
                    "unit_price": amount,
                }
            ],
        }
        config_online = self._config_online(request.back_urls or self._back_urls())
        if config_online:
            payload["config"] = {"online": config_online}

        response = self._request(
            "POST",
            _ORDERS_PATH,
            json=payload,
            idempotency_key=request.idempotency_key,
            expected=(200, 201),
        )

        external_id = response.get("id")
        checkout_url = (
            response.get("checkout_url")
            or response.get("init_point")
            or response.get("sandbox_init_point")
        )
        if not external_id or not checkout_url:
            raise PaymentProviderError("Mercado Pago order response is incomplete")
        return CreateCheckoutResult(
            external_id=str(external_id),
            checkout_url=str(checkout_url),
            external_reference=response.get(
                "external_reference", request.external_reference
            ),
        )

    def cancel_checkout(self, request: CancelCheckoutRequest) -> CancelCheckoutResult:
        _body, status_code = self._request_raw(
            "POST",
            f"{_ORDERS_PATH}/{request.external_id}/cancel",
            idempotency_key=request.idempotency_key,
            expected=(200, 201, 204, 404, 409),
        )
        # 404/409 mean the checkout does not exist or was already cancelled:
        # an idempotent success. A 2xx means WE cancelled it now.
        return CancelCheckoutResult(already_cancelled=status_code in (404, 409))

    def get_payment(self, external_id: str) -> ProviderPayment:
        response = self._request("GET", f"{_ORDERS_PATH}/{external_id}", expected=(200,))
        return ProviderPayment(
            external_id=str(response.get("id", external_id)),
            status=map_mercadopago_status(_extract_status(response)),
            external_reference=response.get("external_reference"),
            amount=_decimal_or_none(response.get("total_amount")),
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

    @staticmethod
    def _config_online(back_urls: dict) -> dict:
        """Map the internal success/failure/pending back URLs to `config.online`.

        `auto_return` is only valid when `success_url` is present.
        """
        online: dict[str, str] = {}
        if back_urls.get("success"):
            online["success_url"] = back_urls["success"]
        if back_urls.get("failure"):
            online["failure_url"] = back_urls["failure"]
        if back_urls.get("pending"):
            online["pending_url"] = back_urls["pending"]
        if online.get("success_url"):
            online["auto_return"] = "approved"
        return online

    def _headers(self, idempotency_key: Optional[str]) -> dict:
        headers = {
            "Authorization": f"Bearer {self.settings.access_token}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        return headers

    def _send(self, method: str, path: str, *, json, idempotency_key: Optional[str]):
        try:
            return self._session.request(
                method,
                f"{self.settings.api_base_url}{path}",
                headers=self._headers(idempotency_key),
                json=json,
                timeout=self.settings.request_timeout_seconds,
            )
        except Exception as exc:
            raise PaymentProviderError("Mercado Pago request failed") from exc

    def _request(
        self,
        method: str,
        path: str,
        *,
        json=None,
        idempotency_key: Optional[str] = None,
        expected=(200,),
    ) -> dict:
        body, _ = self._request_raw(
            method, path, json=json, idempotency_key=idempotency_key, expected=expected
        )
        return body

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        json=None,
        idempotency_key: Optional[str] = None,
        expected=(200,),
    ) -> tuple[dict, int]:
        response = self._send(method, path, json=json, idempotency_key=idempotency_key)
        status_code = response.status_code
        if status_code not in expected:
            # Diagnostics for dev/logs: HTTP status + provider error code/message.
            # Never a secret: the Authorization header is not logged.
            logger.warning(
                "Mercado Pago request failed: method=%s path=%s status=%s error=%s",
                method,
                path,
                status_code,
                _error_summary(response),
            )
            raise PaymentProviderError("Mercado Pago request failed")
        try:
            body = response.json()
        except Exception as exc:
            raise PaymentProviderError("Mercado Pago response is invalid") from exc
        return (body if isinstance(body, dict) else {}), status_code


def _error_summary(response: Any) -> str:
    """Compact, secret-free summary of a failed Mercado Pago response."""
    try:
        body = response.json()
    except Exception:
        return "<non-json body>"
    if isinstance(body, dict):
        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            return "; ".join(
                f"{e.get('code', '?')}: {e.get('message', '')} "
                f"{e.get('details', '')}"
                for e in errors
                if isinstance(e, dict)
            )[:1000]
    return str(body)[:1000]


def _extract_status(response: dict) -> str:
    transactions = response.get("transactions") or {}
    payments = transactions.get("payments") or []
    if payments:
        return str(payments[0].get("status", "")).lower()
    return str(response.get("status", "")).lower()


def _amount_str(value: Decimal) -> str:
    return f"{Decimal(value):.2f}"


def _decimal_or_none(value) -> Optional[Decimal]:
    return Decimal(str(value)) if value is not None else None
