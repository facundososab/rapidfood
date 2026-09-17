"""Adapts the order module's public driver ports to `OrderServicePort`.

Cross-context boundary: only the sibling's `application.ports` are imported and
the results are mapped into conversation-owned DTOs. Order rules (pricing,
reopen, transitions, cancellability) stay entirely on the order side.

After a mutation that superseded a checkout (a reopen), the remote cancellation
is attempted here, AFTER the local transaction committed, and is best-effort:
local consistency never depends on the provider call.
"""
from __future__ import annotations

import functools
from typing import Any, Optional

from modules.conversation.domain.errors import AgentBusinessError
from modules.conversation.application.ports.driven.order_service import (
    CheckoutDTO,
    CurrentOrderDTO,
    OrderLineDTO,
    OrderLineModifierDTO,
    OrderLineRemovedIngredientDTO,
    OrderMutationDTO,
    OrderServicePort,
    OrderStatusDTO,
    OrderSummaryDTO,
)
from modules.order.application.ports.driver.add_item_to_order_port import (
    AddItemToOrderCommand,
)
from modules.order.application.ports.driver.apply_coupon_to_order_port import (
    ApplyCouponToOrderCommand,
)
from modules.order.application.ports.driver.cancel_order_ports import CancelOrderCommand
from modules.order.application.ports.driver.confirm_order_ports import ConfirmOrderCommand
from modules.order.application.ports.driver.get_current_order_port import (
    GetCurrentOrderQuery,
)
from modules.order.application.ports.driver.get_latest_active_order_port import (
    GetLatestActiveOrderQuery,
)
from modules.order.application.ports.driver.get_or_create_current_draft_port import (
    GetOrCreateCurrentDraftCommand,
)
from modules.order.application.ports.driver.payment_ports import (
    CancelSupersededCheckoutCommand,
    CreatePaymentCheckoutCommand,
)
from modules.order.application.ports.driver.remove_item_from_order_port import (
    RemoveItemFromOrderCommand,
)
from modules.order.application.ports.driver.set_delivery_for_order_port import (
    SetDeliveryForOrderCommand,
)
from modules.order.application.ports.driver.set_payment_type_port import (
    SetPaymentTypeCommand as OrderSetPaymentTypeCommand,
)
from modules.order.application.ports.driver.set_client_for_order_port import (
    SetClientForOrderCommand,
)
from modules.order.application.ports.driver.set_pickup_for_order_port import (
    SetPickupForOrderCommand,
)
from modules.order.application.ports.driver.update_item_in_order_port import (
    UpdateItemInOrderCommand,
)
from modules.order.application.ports.driver.order_errors import OrderDomainError



# Order business errors -> stable codes the agent can explain to the customer.
_ORDER_ERROR_CODES = {
    "NewOrderRequiredError": "NEW_ORDER_REQUIRED",
    "OrderNotFound": "ORDER_NOT_FOUND",
    "OrderNotModifiableError": "ORDER_NOT_MODIFIABLE",
    "OrderStateError": "ORDER_STATE_INVALID",
    "InvalidLineError": "INVALID_LINE",
    "InvalidCouponError": "INVALID_COUPON",
    "ModifierValidationError": "INVALID_MODIFIER_SELECTION",
    "IngredientNotRemovableError": "INGREDIENT_NOT_REMOVABLE",
    "DeliveryNotAvailableError": "DELIVERY_OUTSIDE_ZONE",
    "DeliveryAddressRequiredError": "DELIVERY_ADDRESS_REQUIRED",
    "DeliveryQuoteFailedError": "DELIVERY_PROVIDER_ERROR",
    "MinimumOrderNotMetError": "MINIMUM_ORDER_NOT_REACHED",
    "OrderClientRequiredError": "ORDER_CLIENT_REQUIRED",
    "BusinessClosedError": "BUSINESS_CLOSED",
    "InvalidPaymentTypeError": "INVALID_PAYMENT_TYPE",
    "PaymentAttemptNotFoundError": "PAYMENT_ATTEMPT_NOT_FOUND",
}


def _translate_order_errors(method):
    """Translate an order business error into a conversation business error.

    Keeps the cross-context boundary honest: conversation never imports the
    order domain, and the agent receives a stable business code.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except OrderDomainError as exc:
            code = _ORDER_ERROR_CODES.get(type(exc).__name__, "ORDER_ERROR")
            raise AgentBusinessError(str(exc), code=code) from exc

    return wrapper


class OrderServiceAdapter(OrderServicePort):
    def __init__(
        self,
        *,
        get_current_order: Any,
        get_latest_active_order: Any,
        get_order_summary: Any,
        get_or_create_current_draft: Any,
        add_item: Any,
        update_item: Any,
        remove_item: Any,
        set_delivery: Any,
        set_pickup: Any,
        set_payment_type: Any,
        set_client: Any,
        apply_coupon: Any,
        confirm_order: Any,
        cancel_order: Any,
        create_payment_checkout: Any,
        cancel_superseded_checkout: Any,
    ) -> None:
        self._get_current_order = get_current_order
        self._get_latest_active_order = get_latest_active_order
        self._get_order_summary = get_order_summary
        self._get_or_create_current_draft = get_or_create_current_draft
        self._add_item = add_item
        self._update_item = update_item
        self._remove_item = remove_item
        self._set_delivery = set_delivery
        self._set_pickup = set_pickup
        self._set_payment_type = set_payment_type
        self._set_client = set_client
        self._apply_coupon = apply_coupon
        self._confirm_order = confirm_order
        self._cancel_order = cancel_order
        self._create_payment_checkout = create_payment_checkout
        self._cancel_superseded_checkout = cancel_superseded_checkout

    # --- reads -----------------------------------------------------------
    @_translate_order_errors
    def get_current_order(self, business_config_id, conversation_id) -> CurrentOrderDTO:
        result = self._get_current_order.execute(
            GetCurrentOrderQuery(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
            )
        )
        if not result.found or result.order is None:
            return CurrentOrderDTO(found=False)
        order = result.order
        return CurrentOrderDTO(
            found=True,
            order_id=order.id,
            status=order.status.value,
            version=order.version,
            editable=result.editable,
            requires_reopen=result.requires_reopen,
            requires_new_order=result.requires_new_order,
        )

    @_translate_order_errors
    def get_latest_active_order(self, business_config_id, client_id=None, conversation_id=None):
        order = self._get_latest_active_order.execute(
            GetLatestActiveOrderQuery(
                business_config_id=business_config_id,
                client_id=client_id,
                conversation_id=conversation_id,
            )
        )
        if order is None:
            return None
        return OrderStatusDTO(
            order_id=order.id,
            status=order.status.value,
            estimated_time=order.estimated_time,
            total_amount=(
                str(order.total_amount) if order.total_amount is not None else None
            ),
        )

    @_translate_order_errors
    def get_order_summary(self, order_id) -> OrderSummaryDTO:
        summary = self._get_order_summary.execute(order_id)
        return OrderSummaryDTO(
            order_id=summary.order_id,
            status=summary.status,
            version=summary.version,
            lines=tuple(
                OrderLineDTO(
                    line_id=line.line_id,
                    product_variant_id=line.product_variant_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    subtotal=line.subtotal,
                    modifiers=tuple(
                        OrderLineModifierDTO(
                            id=m["id"], name=m["name"], price_delta=m.get("price_delta")
                        )
                        for m in line.modifiers
                    ),
                    removed_ingredients=tuple(
                        OrderLineRemovedIngredientDTO(id=r["id"], name=r["name"])
                        for r in line.removed_ingredients
                    ),
                )
                for line in summary.lines
            ),
            subtotal=summary.subtotal,
            discount=summary.discount,
            shipping_cost=summary.shipping_cost,
            total_amount=summary.total_amount,
            delivery_type=summary.delivery_type,
            address=summary.address,
            payment_type=summary.payment_type,
            estimated_time=summary.estimated_time,
            missing_requirements=tuple(summary.missing_requirements),
        )

    @_translate_order_errors
    def get_or_create_current_draft(
        self, *, business_config_id, conversation_id, client_id=None, client_name=None
    ) -> str:
        result = self._get_or_create_current_draft.execute(
            GetOrCreateCurrentDraftCommand(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
                client_id=client_id,
                client_name=client_name,
                # Conversation is the agent channel: its drafts are AGENT orders,
                # so confirming waits for settlement instead of being accepted
                # immediately like a manual (in place) order.
                origin="AGENT",
            )
        )
        return result.order_id

    # --- mutations -------------------------------------------------------
    @_translate_order_errors
    def add_item(
        self, *, business_config_id, conversation_id, external_message_id,
        order_id, product_variant_id, quantity, modifier_option_ids,
        removed_ingredient_ids,
    ) -> OrderMutationDTO:
        response = self._add_item.execute(
            AddItemToOrderCommand(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                order_id=order_id,
                product_variant_id=product_variant_id,
                quantity=quantity,
                modifier_option_ids=list(modifier_option_ids),
                removed_ingredient_ids=list(removed_ingredient_ids),
            )
        )
        self._cancel_superseded(response.superseded_attempt_ids)
        return _mutation(response)

    @_translate_order_errors
    def update_item(
        self, *, business_config_id, conversation_id, external_message_id,
        order_id, line_id, quantity=None, modifier_option_ids=None,
        removed_ingredient_ids=None,
    ) -> OrderMutationDTO:
        response = self._update_item.execute(
            UpdateItemInOrderCommand(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                order_id=order_id,
                line_id=line_id,
                quantity=quantity,
                modifier_option_ids=modifier_option_ids,
                removed_ingredient_ids=removed_ingredient_ids,
            )
        )
        self._cancel_superseded(response.superseded_attempt_ids)
        return _mutation(response)

    @_translate_order_errors
    def remove_item(
        self, *, business_config_id, conversation_id, external_message_id,
        order_id, line_id,
    ) -> OrderMutationDTO:
        response = self._remove_item.execute(
            RemoveItemFromOrderCommand(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                order_id=order_id,
                line_id=line_id,
            )
        )
        self._cancel_superseded(response.superseded_attempt_ids)
        return _mutation(response)

    @_translate_order_errors
    def set_delivery(
        self, *, business_config_id, conversation_id, external_message_id,
        order_id, address,
    ) -> OrderMutationDTO:
        response = self._set_delivery.execute(
            SetDeliveryForOrderCommand(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                order_id=order_id,
                street=address.get("street"),
                street_number=address.get("street_number"),
                floor=address.get("floor"),
                apartment=address.get("apartment"),
                city=address.get("city"),
                province=address.get("province"),
                postal_code=address.get("postal_code"),
            )
        )
        self._cancel_superseded(response.superseded_attempt_ids)
        return _mutation(response)

    @_translate_order_errors
    def set_pickup(
        self, *, business_config_id, conversation_id, external_message_id, order_id
    ) -> OrderMutationDTO:
        response = self._set_pickup.execute(
            SetPickupForOrderCommand(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                order_id=order_id,
            )
        )
        self._cancel_superseded(response.superseded_attempt_ids)
        return _mutation(response)

    @_translate_order_errors
    def set_payment_type(self, order_id: str, payment_type: str) -> None:
        self._set_payment_type.execute(
            OrderSetPaymentTypeCommand(order_id=order_id, payment_type=payment_type)
        )

    @_translate_order_errors
    def set_client(self, order_id, client_name=None, client_id=None) -> None:
        self._set_client.execute(
            SetClientForOrderCommand(
                order_id=order_id, client_name=client_name, client_id=client_id
            )
        )

    @_translate_order_errors
    def apply_coupon(
        self, *, business_config_id, conversation_id, external_message_id,
        order_id, coupon_code,
    ) -> OrderMutationDTO:
        response = self._apply_coupon.execute(
            ApplyCouponToOrderCommand(
                business_config_id=business_config_id,
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                order_id=order_id,
                coupon_code=coupon_code,
            )
        )
        self._cancel_superseded(response.superseded_attempt_ids)
        return _mutation(response)

    @_translate_order_errors
    def confirm_order(self, order_id: str) -> OrderStatusDTO:
        response = self._confirm_order.execute(ConfirmOrderCommand(order_id=order_id))
        return OrderStatusDTO(order_id=response.order_id, status=response.status)

    @_translate_order_errors
    def cancel_order(self, order_id: str) -> OrderStatusDTO:
        response = self._cancel_order.execute(CancelOrderCommand(order_id=order_id))
        return OrderStatusDTO(order_id=response.order_id, status=response.status)

    @_translate_order_errors
    def create_payment_checkout(self, order_id: str) -> CheckoutDTO:
        response = self._create_payment_checkout.execute(
            CreatePaymentCheckoutCommand(order_id=order_id)
        )
        return CheckoutDTO(
            order_id=response.order_id,
            checkout_url=response.checkout_url,
            payment_attempt_id=response.payment_attempt_id,
            status=response.status,
            order_version=response.order_version,
        )

    def _cancel_superseded(self, attempt_ids) -> None:
        """Best-effort remote cancellation; never blocks the local result."""
        for attempt_id in attempt_ids or ():
            try:
                self._cancel_superseded_checkout.execute(
                    CancelSupersededCheckoutCommand(payment_attempt_id=attempt_id)
                )
            except Exception:
                # Local consistency does not depend on the provider call; the
                # attempt stays superseded + retryable.
                continue


def _mutation(response) -> OrderMutationDTO:
    return OrderMutationDTO(
        order_id=response.order_id,
        version=getattr(response, "version", 0),
        replayed=response.replayed,
        line_id=getattr(response, "line_id", None),
        line_count=getattr(response, "line_count", None),
        total_amount=getattr(response, "total_amount", None),
        shipping_cost=getattr(response, "shipping_cost", None),
    )
