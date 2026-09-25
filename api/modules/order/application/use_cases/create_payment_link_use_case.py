from typing import Optional

from modules.order.application.ports.driver.payment_ports import (
    CreatePaymentLinkCommand,
    CreatePaymentLinkPort,
    CreatePaymentLinkResult,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.payment_credentials_query import (
    PaymentCredentialsQuery,
)
from modules.order.application.ports.driven.payment_provider import (
    CreateCheckoutLinkRequest,
    PaymentProvider,
)
from modules.order.application.ports.driven.payment_repository import PaymentRepository
from modules.order.domain.errors.order_errors import OrderNotFound, OrderStateError
from modules.order.domain.models.order import Order
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


class CreatePaymentLinkUseCase(CreatePaymentLinkPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_repo: PaymentRepository,
        payment_provider: PaymentProvider,
        currency: str = "ARS",
        provider_name: str = "MERCADOPAGO",
        credentials_query: Optional[PaymentCredentialsQuery] = None,
    ) -> None:
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.payment_provider = payment_provider
        self.currency = currency
        self.provider_name = provider_name
        self.credentials_query = credentials_query

    def execute(self, command: CreatePaymentLinkCommand) -> CreatePaymentLinkResult:
        order = self.order_repo.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFound("Order not found")
        if order.status != OrderState.PENDING:
            raise OrderStateError("Only PENDING orders can create payment links")
        if order.payment_type != PaymentMethod.ONLINE:
            raise ValueError("Only ONLINE orders can create payment links")
        if order.total_amount is None or order.total_amount <= 0:
            raise ValueError("Order must have a positive total")

        access_token = self._resolve_access_token(order)

        external_reference = order.id
        payment = self.payment_repo.create_pending(
            order_id=order.id,
            provider=self.provider_name,
            amount=order.total_amount,
            external_reference=external_reference,
        )
        provider_result = self.payment_provider.create_checkout_link(
            CreateCheckoutLinkRequest(
                order_id=order.id,
                payment_id=payment.id,
                amount=order.total_amount,
                currency=self.currency,
                external_reference=external_reference,
                access_token=access_token,
            )
        )

        payment.external_id = provider_result.external_id
        payment.preference_id = provider_result.preference_id
        payment.checkout_url = provider_result.checkout_url
        payment.external_reference = provider_result.external_reference
        saved_payment = self.payment_repo.save(payment)

        return CreatePaymentLinkResult(
            order_id=order.id,
            payment_id=saved_payment.id,
            provider=saved_payment.provider,
            checkout_url=saved_payment.checkout_url or "",
            status=saved_payment.status.value,
        )

    def _resolve_access_token(self, order: Order) -> Optional[str]:
        """Resolve the business credentials, falling back to the global token."""
        if self.credentials_query is None:
            return None
        business_config_id = getattr(order, "business_config_id", None)
        if not business_config_id:
            return None
        return self.credentials_query.get_access_token(business_config_id)
