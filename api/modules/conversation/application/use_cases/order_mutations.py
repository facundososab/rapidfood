"""Conversation order mutations.

Each use case resolves the current order from the trusted context (creating the
draft when there is none) and delegates to the order module's reopen-aware,
idempotent mutations. ``NEW_ORDER_REQUIRED`` is surfaced as a business error so
the agent asks the customer before starting a new order (which may imply a new
delivery and shipping cost).
"""
from __future__ import annotations

from modules.conversation.application.address_defaults import (
    complete_address,
    require_deliverable_address,
)
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driven.order_service import (
    CheckoutDTO,
    OrderMutationDTO,
    OrderServicePort,
    OrderStatusDTO,
)
from modules.conversation.application.ports.driver.agent_commands import (
    AddItemCommand,
    ApplyCouponCommand,
    RemoveItemCommand,
    SetClientCommand,
    SetDeliveryCommand,
    SetPaymentTypeCommand,
    UpdateItemCommand,
)
from modules.conversation.domain.errors import (
    ConversationValidationError,
    NewOrderRequiredError,
)


def _message_id(context: AgentExecutionContext) -> str:
    if not context.external_message_id:
        raise ConversationValidationError(
            "external_message_id is required for write operations"
        )
    return context.external_message_id


def _resolve_order_id(order_service: OrderServicePort, context: AgentExecutionContext) -> str:
    """The order to mutate: the current editable one, or a fresh draft.

    Never creates an order when the previous one is closed — that decision is
    the customer's (it may change delivery and cost).
    """
    current = order_service.get_current_order(
        context.business_configuration_id, context.conversation_id
    )
    if not current.found:
        return order_service.get_or_create_current_draft(
            business_config_id=context.business_configuration_id,
            conversation_id=context.conversation_id,
            client_id=context.client_id,
        )
    if current.editable and current.order_id is not None:
        return current.order_id
    raise NewOrderRequiredError(
        "El pedido anterior ya está cerrado. Para esto hace falta un pedido nuevo."
    )


class _MutationUseCase:
    def __init__(self, order_service: OrderServicePort) -> None:
        self._order_service = order_service

    def _resolve(self, context: AgentExecutionContext) -> str:
        return _resolve_order_id(self._order_service, context)


class AddItemToConversationOrderUseCase(_MutationUseCase):
    def execute(
        self, command: AddItemCommand, context: AgentExecutionContext
    ) -> OrderMutationDTO:
        return self._order_service.add_item(
            business_config_id=context.business_configuration_id,
            conversation_id=context.conversation_id,
            external_message_id=_message_id(context),
            order_id=self._resolve(context),
            product_variant_id=command.product_variant_id,
            quantity=command.quantity,
            modifier_option_ids=list(command.modifier_option_ids),
            removed_ingredient_ids=list(command.removed_ingredient_ids),
        )


class UpdateItemInConversationOrderUseCase(_MutationUseCase):
    def execute(
        self, command: UpdateItemCommand, context: AgentExecutionContext
    ) -> OrderMutationDTO:
        return self._order_service.update_item(
            business_config_id=context.business_configuration_id,
            conversation_id=context.conversation_id,
            external_message_id=_message_id(context),
            order_id=self._resolve(context),
            line_id=command.line_id,
            quantity=command.quantity,
            modifier_option_ids=(
                list(command.modifier_option_ids)
                if command.modifier_option_ids is not None
                else None
            ),
            removed_ingredient_ids=(
                list(command.removed_ingredient_ids)
                if command.removed_ingredient_ids is not None
                else None
            ),
        )


class RemoveItemFromConversationOrderUseCase(_MutationUseCase):
    def execute(
        self, command: RemoveItemCommand, context: AgentExecutionContext
    ) -> OrderMutationDTO:
        return self._order_service.remove_item(
            business_config_id=context.business_configuration_id,
            conversation_id=context.conversation_id,
            external_message_id=_message_id(context),
            order_id=self._resolve(context),
            line_id=command.line_id,
        )


class SetDeliveryForConversationOrderUseCase(_MutationUseCase):
    def __init__(self, order_service: OrderServicePort, business_service=None) -> None:
        super().__init__(order_service)
        self._business_service = business_service

    def execute(
        self, command: SetDeliveryCommand, context: AgentExecutionContext
    ) -> OrderMutationDTO:
        defaults = (
            self._business_service.get_address(context.business_configuration_id)
            if self._business_service is not None
            else None
        )
        address = require_deliverable_address(
            complete_address(command.address, defaults)
        )
        return self._order_service.set_delivery(
            business_config_id=context.business_configuration_id,
            conversation_id=context.conversation_id,
            external_message_id=_message_id(context),
            order_id=self._resolve(context),
            address=address.as_dict(),
        )


class SetPickupForConversationOrderUseCase(_MutationUseCase):
    def execute(self, context: AgentExecutionContext) -> OrderMutationDTO:
        return self._order_service.set_pickup(
            business_config_id=context.business_configuration_id,
            conversation_id=context.conversation_id,
            external_message_id=_message_id(context),
            order_id=self._resolve(context),
        )


class SetClientForConversationOrderUseCase(_MutationUseCase):
    """Attach the customer's name (and, when a phone is given, a registered client).

    Must happen BEFORE asking for confirmation: the order needs to be attributable
    to close it.
    """

    def __init__(self, order_service: OrderServicePort, client_service=None) -> None:
        super().__init__(order_service)
        self._client_service = client_service

    def execute(self, command: SetClientCommand, context: AgentExecutionContext) -> dict:
        order_id = self._resolve(context)
        client_id = None
        if command.phone_number and self._client_service is not None:
            client_id = self._client_service.resolve_client(
                command.name, command.phone_number
            )
        self._order_service.set_client(
            order_id, client_name=command.name, client_id=client_id
        )
        return {
            "order_id": order_id,
            "client_name": command.name.strip(),
            "client_linked": client_id is not None,
        }


class SetPaymentTypeForConversationOrderUseCase(_MutationUseCase):
    def execute(
        self, command: SetPaymentTypeCommand, context: AgentExecutionContext
    ) -> None:
        self._order_service.set_payment_type(self._resolve(context), command.payment_type)


class ApplyCouponForConversationOrderUseCase(_MutationUseCase):
    def execute(
        self, command: ApplyCouponCommand, context: AgentExecutionContext
    ) -> OrderMutationDTO:
        return self._order_service.apply_coupon(
            business_config_id=context.business_configuration_id,
            conversation_id=context.conversation_id,
            external_message_id=_message_id(context),
            order_id=self._resolve(context),
            coupon_code=command.coupon_code,
        )


class ConfirmConversationOrderUseCase(_MutationUseCase):
    """Confirm the current order.

    Policy (enforced by the tool/prompt, not here): the agent may only call this
    after presenting the up-to-date summary and receiving explicit confirmation
    of THAT summary.
    """

    def execute(self, context: AgentExecutionContext) -> OrderStatusDTO:
        return self._order_service.confirm_order(self._resolve(context))


class CancelConversationOrderUseCase(_MutationUseCase):
    def execute(self, context: AgentExecutionContext) -> OrderStatusDTO:
        current = self._order_service.get_current_order(
            context.business_configuration_id, context.conversation_id
        )
        if not current.found or current.order_id is None:
            raise NewOrderRequiredError("No hay un pedido activo para cancelar.")
        # Cancellability is decided entirely by the order module.
        return self._order_service.cancel_order(current.order_id)


class CreateCheckoutForConversationOrderUseCase(_MutationUseCase):
    def execute(self, context: AgentExecutionContext) -> CheckoutDTO:
        return self._order_service.create_payment_checkout(self._resolve(context))
