"""Handle a provider webhook (Mercado Pago notification).

The provider state is ALWAYS fetched authoritatively; the raw payload status is
never trusted. The attempt is resolved by its provider external identifier (not
"the current attempt"). An APPROVED notification only pays the order when it
matches the order's CURRENT version, the expected amount, and the attempt is not
superseded — this is the definitive local barrier when a remote cancellation of
an old checkout failed and it still got paid.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from modules.order.application.ports.driven.order_paid_notifier import (
    OrderPaidNotifierPort,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.payment_credentials_query import (
    PaymentCredentialsQuery,
)
from modules.order.application.ports.driven.payment_provider import PaymentProviderPort
from modules.order.application.ports.driven.payment_repository import (
    PaymentAttemptRepository,
)
from modules.order.application.ports.driver.payment_ports import (
    HandlePaymentWebhookCommand,
    HandlePaymentWebhookPort,
    HandlePaymentWebhookResult,
)
from modules.order.domain.errors.order_errors import (
    OrderNotFound,
    PaymentAttemptNotFoundError,
)
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_attempt import PaymentAttempt
from modules.order.domain.models.payment_method import PaymentMethod
from modules.order.domain.models.payment_status import PaymentStatus
from modules.order.domain.services.state_transitions import can_transition


logger = logging.getLogger(__name__)


class HandlePaymentWebhookUseCase(HandlePaymentWebhookPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentAttemptRepository,
        payment_provider: PaymentProviderPort,
        paid_notifier: Optional[OrderPaidNotifierPort] = None,
        credentials_query: Optional[PaymentCredentialsQuery] = None,
    ) -> None:
        self._order_repo = order_repo
        self._payment_repo = payment_repo
        self._payment_provider = payment_provider
        self._paid_notifier = paid_notifier
        self._credentials_query = credentials_query

    def execute(self, command: HandlePaymentWebhookCommand) -> HandlePaymentWebhookResult:
        remote = self._payment_provider.get_payment(
            command.data_id,
            access_token=self._resolve_access_token(command.data_id),
        )
        if remote is None:
            # The provider does not know this id (simulated/unknown): acknowledge
            # it so Mercado Pago stops retrying, and apply no local effect.
            return HandlePaymentWebhookResult(
                payment_attempt_id=None,
                status="UNKNOWN",
                order_id=None,
                order_status=None,
                processed=False,
                applied=False,
            )

        attempt = self._payment_repo.get_by_external_id(remote.external_id)
        if attempt is None:
            raise PaymentAttemptNotFoundError(
                f"No payment attempt for provider id {remote.external_id}"
            )

        order = self._order_repo.get_by_id(attempt.order_id)
        if order is None:
            raise OrderNotFound("Order not found")

        # Persist the provider status even for a stale attempt: it really was
        # approved, and we keep it for refund/reconciliation.
        if not attempt.has_same_final_status(remote.status):
            attempt.update_provider_status(remote.status)
            attempt = self._payment_repo.save(attempt)

        applied = False
        if remote.status is PaymentStatus.APPROVED and self._pays_current_order(
            attempt, order, remote.amount
        ):
            if can_transition(order.status, OrderState.PAID, order.payment_type):
                order.status = OrderState.PAID
                self._order_repo.save(order)
                applied = True

        if applied:
            self._notify_paid(order)

        return HandlePaymentWebhookResult(
            payment_attempt_id=attempt.id,
            status=attempt.status.value,
            order_id=order.id,
            order_status=order.status.value,
            processed=True,
            applied=applied,
        )

    def _resolve_access_token(self, data_id: str) -> Optional[str]:
        """Resolve the business token that owns the notified payment attempt.

        The provider call is the FIRST remote hop, so the attempt must be peeked
        locally by its provider external id to find the owning business. A
        missing attempt/order, an unlinked business or a linkage failure all
        degrade to ``None`` (the configured token) instead of breaking the
        webhook: credentials are an optional enrichment, never a precondition.
        """
        if self._credentials_query is None:
            return None
        try:
            local = self._payment_repo.get_by_external_id(data_id)
            if local is None:
                return None
            order = self._order_repo.get_by_id(local.order_id)
            if order is None:
                return None
            return self._credentials_query.get_access_token(
                order.business_config_id or "default"
            )
        except Exception:
            logger.warning(
                "Per-business payment credentials unavailable (data_id=%s); "
                "falling back to the configured token.",
                data_id,
                exc_info=True,
            )
            return None

    def _notify_paid(self, order) -> None:
        """Best-effort, POST-COMMIT customer notification; never breaks the webhook."""
        if self._paid_notifier is None or not order.conversation_id:
            return
        try:
            self._paid_notifier.notify_order_paid(
                conversation_id=order.conversation_id, order_id=order.id
            )
        except Exception:
            logger.exception(
                "Order paid notification failed (order=%s)", order.id
            )

    @staticmethod
    def _pays_current_order(
        attempt: PaymentAttempt, order, remote_amount: Decimal | None
    ) -> bool:
        if order.status is not OrderState.PENDING:
            return False
        if order.payment_type is not PaymentMethod.ONLINE:
            return False
        if not attempt.is_current_for(order.version):
            return False
        if remote_amount is None or order.total_amount is None:
            return False
        return Decimal(str(remote_amount)) == Decimal(str(order.total_amount))
