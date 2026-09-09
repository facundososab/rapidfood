from modules.order.application.ports.driver.payment_ports import (
    ProcessPaymentNotificationCommand,
    ProcessPaymentNotificationPort,
    ProcessPaymentNotificationResult,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.payment_provider import PaymentProvider
from modules.order.application.ports.driven.payment_repository import PaymentRepository
from modules.order.domain.errors.order_errors import OrderNotFound
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus


class ProcessPaymentNotificationUseCase(ProcessPaymentNotificationPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
        payment_provider: PaymentProvider,
    ) -> None:
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.payment_provider = payment_provider

    def execute(
        self, command: ProcessPaymentNotificationCommand
    ) -> ProcessPaymentNotificationResult:
        remote_payment = self.payment_provider.get_payment(command.data_id)
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
