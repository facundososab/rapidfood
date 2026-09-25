import logging
from typing import Optional

from modules.order.application.ports.driver.payment_ports import (
    ProcessPaymentNotificationCommand,
    ProcessPaymentNotificationPort,
    ProcessPaymentNotificationResult,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.payment_credentials_query import (
    PaymentCredentialsQuery,
)
from modules.order.application.ports.driven.payment_provider import PaymentProvider
from modules.order.application.ports.driven.payment_repository import PaymentRepository
from modules.order.domain.errors.order_errors import OrderNotFound
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus

logger = logging.getLogger(__name__)


class ProcessPaymentNotificationUseCase(ProcessPaymentNotificationPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
        payment_provider: PaymentProvider,
        credentials_query: Optional[PaymentCredentialsQuery] = None,
    ) -> None:
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.payment_provider = payment_provider
        self.credentials_query = credentials_query

    def execute(
        self, command: ProcessPaymentNotificationCommand
    ) -> ProcessPaymentNotificationResult:
        access_token = self._resolve_access_token(command.data_id)
        remote_payment = self.payment_provider.get_payment(
            command.data_id, access_token=access_token
        )
        payment = self._find_payment(
            remote_payment.external_id,
            remote_payment.preference_id,
            remote_payment.external_reference,
        )
        if payment is None:
            raise ValueError("Payment not found")

        order = self.order_repo.get_by_id(payment.order_id)
        if order is None:
            raise OrderNotFound("Order not found")

        if not payment.has_same_final_status(remote_payment.status):
            payment = self.payment_repo.update_status(payment.id, remote_payment.status)
            if remote_payment.status == PaymentStatus.APPROVED:
                if order.status == OrderState.PENDING:
                    order.status = OrderState.PAID
                    order = self.order_repo.save(order)

        return ProcessPaymentNotificationResult(
            payment_id=payment.id,
            status=payment.status.value,
            order_id=order.id,
            order_status=order.status.value,
            processed=True,
        )

    def _resolve_access_token(self, data_id: str) -> Optional[str]:
        """Resolve the business token of the notified payment, or fall back to env.

        The webhook must keep working when the business, its order or the
        linkage data cannot be read, so any failure degrades to ``None`` and
        the provider uses the globally configured token.
        """
        if self.credentials_query is None:
            return None
        try:
            local_payment = self.payment_repo.get_by_external_id(data_id)
            if local_payment is None:
                return None
            order = self.order_repo.get_by_id(local_payment.order_id)
            if order is None:
                return None
            business_config_id = getattr(order, "business_config_id", None)
            if not business_config_id:
                return None
            return self.credentials_query.get_access_token(business_config_id)
        except Exception as exc:  # the webhook must not break on credential lookup
            logger.warning(
                "Mercado Pago credentials unavailable for payment %s (%s); "
                "falling back to the configured token.",
                data_id,
                exc,
            )
            return None

    def _find_payment(
        self,
        external_id: str,
        preference_id: str | None,
        external_reference: str | None,
    ) -> Payment | None:
        payment = self.payment_repo.get_by_external_id(external_id)
        if payment is not None:
            return payment
        if preference_id:
            payment = self.payment_repo.get_by_preference_id(preference_id)
            if payment is not None:
                return payment
        if external_reference:
            return self.payment_repo.get_by_external_reference(external_reference)
        return None
