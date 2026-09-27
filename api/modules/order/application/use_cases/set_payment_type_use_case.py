from modules.order.application.ports.driver.set_payment_type_port import (
    SetPaymentTypeCommand,
    SetPaymentTypePort,
    SetPaymentTypeResponse,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.domain.errors.order_errors import (
    InvalidPaymentTypeError,
    OrderNotFound,
    OrderNotModifiableError,
)
from modules.order.domain.models.order_state import OrderState
from modules.order.domain.models.payment_method import PaymentMethod


class SetPaymentTypeUseCase(SetPaymentTypePort):
    """Set how the order will be paid (CASH | ONLINE).

    Only valid while the order is a DRAFT: the payment method is part of the
    snapshot the customer confirms, and the confirmation asks for it before
    leaving DRAFT.
    """

    def __init__(self, order_repo: OrderRepository) -> None:
        self.order_repo = order_repo

    def execute(self, command: SetPaymentTypeCommand) -> SetPaymentTypeResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if order is None:
            raise OrderNotFound("Order not found")

        try:
            payment_type = PaymentMethod(command.payment_type)
        except (ValueError, KeyError):
            raise InvalidPaymentTypeError(
                f"'{command.payment_type}' is not a valid payment type"
            )

        if order.status is not OrderState.DRAFT:
            raise OrderNotModifiableError(
                "The payment type can only be set while the order is a draft"
            )

        order.payment_type = payment_type
        self.order_repo.save(order)

        return SetPaymentTypeResponse(
            order_id=order.id,
            payment_type=order.payment_type.value,
        )
