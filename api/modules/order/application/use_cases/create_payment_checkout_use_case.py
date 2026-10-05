"""Create the Checkout Pro checkout for an ONLINE order awaiting payment.

Flow (a pending checkout does NOT block the draft, but a checkout is only
created for a confirmed order):

    ensure current Order/version
    get/create the single logical PaymentAttempt for that version
    persist the provider idempotency key
    -> POST /v1/orders (X-Idempotency-Key)

If the provider creates the order but the response is lost, the retry finds the
same attempt and reuses the same key, so no second logical checkout is created.
"""
from __future__ import annotations

import logging
from typing import Optional

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.payment_credentials_query import (
    PaymentCredentialsQuery,
)
from modules.order.application.ports.driven.payment_provider import (
    CreateCheckoutRequest,
    PaymentProviderPort,
)
from modules.order.application.ports.driven.payment_repository import (
    PaymentAttemptRepository,
)
from modules.order.application.ports.driver.payment_ports import (
    CreatePaymentCheckoutCommand,
    CreatePaymentCheckoutPort,
    CreatePaymentCheckoutResult,
)
from modules.order.domain.errors.order_errors import (
    OnlinePaymentRequiredError,
    OrderNotConfirmedError,
    OrderNotFound,
    OrderStateError,
    PaymentTypeRequiredError,
)
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod

_PROVIDER_NAME = "MERCADOPAGO"

logger = logging.getLogger(__name__)


class CreatePaymentCheckoutUseCase(CreatePaymentCheckoutPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentAttemptRepository,
        payment_provider: PaymentProviderPort,
        currency: str = "ARS",
        provider_name: str = _PROVIDER_NAME,
        credentials_query: Optional[PaymentCredentialsQuery] = None,
    ) -> None:
        self._order_repo = order_repo
        self._payment_repo = payment_repo
        self._payment_provider = payment_provider
        self._currency = currency
        self._provider_name = provider_name
        self._credentials_query = credentials_query

    def execute(
        self, command: CreatePaymentCheckoutCommand
    ) -> CreatePaymentCheckoutResult:
        order = self._order_repo.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFound("Order not found")
        if order.status is not OrderState.PENDING:
            raise OrderNotConfirmedError(
                "Only a confirmed (PENDING) order can create a payment checkout"
            )
        if order.payment_type is None:
            raise PaymentTypeRequiredError(
                "The order has no payment type; set it to ONLINE before generating a link"
            )
        if order.payment_type is not PaymentMethod.ONLINE:
            raise OnlinePaymentRequiredError(
                "Only an ONLINE order can create a payment checkout"
            )
        if order.total_amount is None or order.total_amount <= 0:
            raise OrderStateError("Order must have a positive total")

        version = order.version
        attempt = self._payment_repo.find_current_for_version(order.id, version)

        if attempt is not None and attempt.external_id:
            # Already created for this version: replay instead of creating another.
            return _result(order.id, attempt, version, created=False)

        if attempt is None:
            attempt = self._payment_repo.create_for_version(
                order_id=order.id,
                provider=self._provider_name,
                amount=order.total_amount,
                order_version=version,
                external_reference=order.id,
                create_idempotency_key=build_idempotency_key(
                    business_config_id=order.business_config_id or "default",
                    conversation_id=order.conversation_id,
                    external_message_id=f"checkout:{order.id}:{version}",
                    operation_name="create_payment_checkout",
                    args={"order_id": order.id, "version": version},
                ),
            )

        provider_result = self._payment_provider.create_checkout(
            CreateCheckoutRequest(
                order_id=order.id,
                attempt_id=attempt.id,
                amount=attempt.amount,
                currency=self._currency,
                external_reference=attempt.external_reference or order.id,
                idempotency_key=attempt.create_idempotency_key or attempt.id,
                access_token=self._resolve_access_token(order),
            )
        )

        attempt.mark_checkout_created(
            external_id=provider_result.external_id,
            checkout_url=provider_result.checkout_url,
            external_reference=provider_result.external_reference,
        )
        saved = self._payment_repo.save(attempt)

        return _result(order.id, saved, version, created=True)

    def _resolve_access_token(self, order) -> Optional[str]:
        """Resolve the per-business Mercado Pago token, or ``None`` for the global one.

        Credentials are an OPTIONAL enrichment: an unlinked business, a missing
        linkage module or a linkage failure must never block a checkout, so every
        failure degrades to ``None`` and the provider falls back to the token in
        settings.
        """
        if self._credentials_query is None:
            return None
        try:
            return self._credentials_query.get_access_token(
                order.business_config_id or "default"
            )
        except Exception:
            logger.warning(
                "Per-business payment credentials unavailable (order=%s); "
                "falling back to the configured token.",
                order.id,
                exc_info=True,
            )
            return None


def _result(order_id, attempt, version, *, created):
    return CreatePaymentCheckoutResult(
        order_id=order_id,
        payment_attempt_id=attempt.id,
        provider=attempt.provider,
        checkout_url=attempt.checkout_url or "",
        status=attempt.status.value,
        order_version=version,
        created=created,
    )
