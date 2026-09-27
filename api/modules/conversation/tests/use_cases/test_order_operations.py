"""Conversation order reads/mutations and delivery quote (fakes only)."""
import pytest

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driven.delivery_service import (
    DeliveryQuoteDTO,
)
from modules.conversation.application.ports.driven.order_service import (
    CheckoutDTO,
    CurrentOrderDTO,
    OrderMutationDTO,
    OrderStatusDTO,
    OrderSummaryDTO,
)
from modules.conversation.application.ports.driver.agent_commands import (
    AddItemCommand,
    AddressCommand,
    ApplyCouponCommand,
    QuoteDeliveryQuery,
    RemoveItemCommand,
    SetDeliveryCommand,
    SetPaymentTypeCommand,
    UpdateItemCommand,
)
from modules.conversation.application.use_cases.delivery import (
    QuoteDeliveryForConversationUseCase,
)
from modules.conversation.application.use_cases.order_mutations import (
    AddItemToConversationOrderUseCase,
    ApplyCouponForConversationOrderUseCase,
    CancelConversationOrderUseCase,
    ConfirmConversationOrderUseCase,
    CreateCheckoutForConversationOrderUseCase,
    RemoveItemFromConversationOrderUseCase,
    SetDeliveryForConversationOrderUseCase,
    SetPaymentTypeForConversationOrderUseCase,
    SetPickupForConversationOrderUseCase,
    UpdateItemInConversationOrderUseCase,
)
from modules.conversation.application.use_cases.order_reads import (
    GetCurrentOrderForConversationUseCase,
    GetLatestActiveOrderForConversationUseCase,
    GetOrderSummaryForConversationUseCase,
)
from modules.conversation.domain.errors import (
    ConversationValidationError,
    NewOrderRequiredError,
    NoActiveOrderError,
)


class FakeOrderService:
    def __init__(self, current=None, summary=None, status=None):
        self.current = current or CurrentOrderDTO(found=False)
        self.summary = summary
        self.status = status or OrderStatusDTO(order_id="o-1", status="CONFIRMED")
        self.calls = []
        self.created_drafts = 0

    def _record(self, name, **kwargs):
        self.calls.append({"name": name, **kwargs})

    def get_current_order(self, business_config_id, conversation_id):
        self._record("get_current_order", business=business_config_id, conversation=conversation_id)
        return self.current

    def get_latest_active_order(self, business_config_id, client_id=None, conversation_id=None):
        self._record("get_latest_active_order", business=business_config_id, client_id=client_id)
        return self.status

    def get_order_summary(self, order_id):
        self._record("get_order_summary", order_id=order_id)
        return self.summary

    def get_or_create_current_draft(
        self, *, business_config_id, conversation_id, client_id=None, client_name=None
    ):
        self.created_drafts += 1
        self._record("get_or_create_current_draft", business=business_config_id, conversation=conversation_id)
        return "new-order"

    def add_item(self, **kwargs):
        self._record("add_item", **kwargs)
        return OrderMutationDTO(order_id=kwargs["order_id"], version=1, line_id="line-1")

    def update_item(self, **kwargs):
        self._record("update_item", **kwargs)
        return OrderMutationDTO(order_id=kwargs["order_id"], version=2, line_id=kwargs["line_id"])

    def remove_item(self, **kwargs):
        self._record("remove_item", **kwargs)
        return OrderMutationDTO(order_id=kwargs["order_id"], version=2, line_count=0)

    def set_delivery(self, **kwargs):
        self._record("set_delivery", **kwargs)
        return OrderMutationDTO(
            order_id=kwargs["order_id"], version=2, shipping_cost="350", total_amount="1350"
        )

    def set_pickup(self, **kwargs):
        self._record("set_pickup", **kwargs)
        return OrderMutationDTO(order_id=kwargs["order_id"], version=2)

    def set_payment_type(self, order_id, payment_type):
        self._record("set_payment_type", order_id=order_id, payment_type=payment_type)

    def apply_coupon(self, **kwargs):
        self._record("apply_coupon", **kwargs)
        return OrderMutationDTO(order_id=kwargs["order_id"], version=2)

    def confirm_order(self, order_id):
        self._record("confirm_order", order_id=order_id)
        self.status = OrderStatusDTO(order_id=order_id, status="PENDING")
        return self.status

    def cancel_order(self, order_id):
        self._record("cancel_order", order_id=order_id)
        return OrderStatusDTO(order_id=order_id, status="CANCELLED")

    def create_payment_checkout(self, order_id):
        self._record("create_payment_checkout", order_id=order_id)
        return CheckoutDTO(
            order_id=order_id,
            checkout_url="https://mp/checkout",
            payment_attempt_id="a-1",
            status="PENDING",
            order_version=7,
        )


class FakeDeliveryService:
    def __init__(self):
        self.calls = []

    def quote_delivery(self, business_configuration_id, destination_address):
        self.calls.append((business_configuration_id, destination_address))
        return DeliveryQuoteDTO(
            available=True, shipping_cost="350", distance_km=3.2, demand_level="LOW"
        )


def _context(**overrides):
    values = dict(
        business_configuration_id="biz-1",
        conversation_id="conv-1",
        channel="LANGSMITH",
        client_id="client-1",
        external_message_id="msg-1",
    )
    values.update(overrides)
    return AgentExecutionContext(**values)


def _editable(order_id="o-1"):
    return CurrentOrderDTO(
        found=True, order_id=order_id, status="DRAFT", version=0, editable=True
    )


def _closed(order_id="o-1"):
    return CurrentOrderDTO(
        found=True,
        order_id=order_id,
        status="PAID",
        version=3,
        editable=False,
        requires_new_order=True,
    )


def test_first_add_item_creates_a_draft_and_adds_the_line():
    service = FakeOrderService(current=CurrentOrderDTO(found=False))
    use_case = AddItemToConversationOrderUseCase(service)

    result = use_case.execute(
        AddItemCommand(product_variant_id="v-1", quantity=1), _context()
    )

    assert result.line_id == "line-1"
    assert service.created_drafts == 1
    added = next(c for c in service.calls if c["name"] == "add_item")
    assert added["order_id"] == "new-order"
    assert added["business_config_id"] == "biz-1"
    assert added["external_message_id"] == "msg-1"


def test_second_add_item_reuses_the_current_order():
    service = FakeOrderService(current=_editable())
    use_case = AddItemToConversationOrderUseCase(service)

    use_case.execute(AddItemCommand(product_variant_id="v-1", quantity=1), _context())

    assert service.created_drafts == 0
    added = next(c for c in service.calls if c["name"] == "add_item")
    assert added["order_id"] == "o-1"


def test_add_item_on_a_closed_order_requires_a_new_order_and_creates_nothing():
    service = FakeOrderService(current=_closed())
    use_case = AddItemToConversationOrderUseCase(service)

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(AddItemCommand(product_variant_id="v-1", quantity=1), _context())

    assert service.created_drafts == 0
    assert [c["name"] for c in service.calls] == ["get_current_order"]


def test_reopenable_pending_order_is_mutated_directly():
    service = FakeOrderService(
        current=CurrentOrderDTO(
            found=True,
            order_id="o-1",
            status="PENDING",
            version=5,
            editable=True,
            requires_reopen=True,
        )
    )
    use_case = AddItemToConversationOrderUseCase(service)

    use_case.execute(AddItemCommand(product_variant_id="v-1", quantity=1), _context())

    assert service.created_drafts == 0


def test_write_without_external_message_id_is_rejected():
    service = FakeOrderService(current=_editable())
    use_case = AddItemToConversationOrderUseCase(service)

    with pytest.raises(ConversationValidationError):
        use_case.execute(
            AddItemCommand(product_variant_id="v-1", quantity=1),
            _context(external_message_id=None),
        )


def test_update_targets_the_line_id():
    service = FakeOrderService(current=_editable())
    use_case = UpdateItemInConversationOrderUseCase(service)

    use_case.execute(
        UpdateItemCommand(line_id="line-9", quantity=3), _context()
    )

    updated = next(c for c in service.calls if c["name"] == "update_item")
    assert updated["line_id"] == "line-9"
    assert updated["quantity"] == 3
    assert updated["modifier_option_ids"] is None


def test_update_can_clear_modifiers_with_an_empty_list():
    service = FakeOrderService(current=_editable())
    use_case = UpdateItemInConversationOrderUseCase(service)

    use_case.execute(
        UpdateItemCommand(line_id="line-9", modifier_option_ids=()),
        _context(),
    )

    updated = next(c for c in service.calls if c["name"] == "update_item")
    assert updated["modifier_option_ids"] == []


def test_remove_item_uses_the_line_id():
    service = FakeOrderService(current=_editable())
    use_case = RemoveItemFromConversationOrderUseCase(service)

    result = use_case.execute(RemoveItemCommand(line_id="line-9"), _context())

    assert result.line_count == 0
    removed = next(c for c in service.calls if c["name"] == "remove_item")
    assert removed["line_id"] == "line-9"


def test_set_delivery_passes_the_address_payload():
    service = FakeOrderService(current=_editable())
    use_case = SetDeliveryForConversationOrderUseCase(service)
    address = AddressCommand(
        street="San Juan", street_number="3250", city="Rosario", province="Santa Fe"
    )

    result = use_case.execute(SetDeliveryCommand(address=address), _context())

    assert result.shipping_cost == "350"
    call = next(c for c in service.calls if c["name"] == "set_delivery")
    assert call["address"]["street"] == "San Juan"
    assert call["address"]["street_number"] == "3250"


def test_set_pickup_delegates():
    service = FakeOrderService(current=_editable())
    use_case = SetPickupForConversationOrderUseCase(service)

    use_case.execute(_context())

    assert any(c["name"] == "set_pickup" for c in service.calls)


def test_set_payment_type_delegates_with_the_domain_value():
    service = FakeOrderService(current=_editable())
    use_case = SetPaymentTypeForConversationOrderUseCase(service)

    use_case.execute(SetPaymentTypeCommand(payment_type="CASH"), _context())

    call = next(c for c in service.calls if c["name"] == "set_payment_type")
    assert call["payment_type"] == "CASH"


def test_apply_coupon_passes_the_code():
    service = FakeOrderService(current=_editable())
    use_case = ApplyCouponForConversationOrderUseCase(service)

    use_case.execute(ApplyCouponCommand(coupon_code="VERANO20"), _context())

    call = next(c for c in service.calls if c["name"] == "apply_coupon")
    assert call["coupon_code"] == "VERANO20"


def test_confirm_uses_the_resolved_order():
    service = FakeOrderService(current=_editable())
    use_case = ConfirmConversationOrderUseCase(service)

    result = use_case.execute(_context())

    assert result.status == "PENDING"
    call = next(c for c in service.calls if c["name"] == "confirm_order")
    assert call["order_id"] == "o-1"


def test_cancel_without_an_order_is_a_business_error():
    service = FakeOrderService(current=CurrentOrderDTO(found=False))
    use_case = CancelConversationOrderUseCase(service)

    with pytest.raises(NewOrderRequiredError):
        use_case.execute(_context())


def test_cancel_delegates_to_the_order_module():
    service = FakeOrderService(current=_closed())
    use_case = CancelConversationOrderUseCase(service)

    result = use_case.execute(_context())

    assert result.status == "CANCELLED"


def test_create_checkout_uses_the_resolved_order():
    service = FakeOrderService(current=_editable())
    use_case = CreateCheckoutForConversationOrderUseCase(service)

    result = use_case.execute(_context())

    assert result.checkout_url == "https://mp/checkout"
    assert result.order_version == 7


def test_get_current_order_reads_with_the_context_scope():
    service = FakeOrderService(current=_editable())
    use_case = GetCurrentOrderForConversationUseCase(service)

    result = use_case.execute(_context())

    assert result.editable is True
    call = service.calls[0]
    assert call["business"] == "biz-1"
    assert call["conversation"] == "conv-1"


def test_latest_active_order_uses_the_client_from_the_context():
    service = FakeOrderService()
    use_case = GetLatestActiveOrderForConversationUseCase(service)

    use_case.execute(_context(client_id="client-7"))

    call = service.calls[0]
    assert call["client_id"] == "client-7"


def test_summary_resolves_the_order_from_the_context():
    service = FakeOrderService(
        current=_editable(),
        summary=OrderSummaryDTO(
            order_id="o-1",
            status="DRAFT",
            version=0,
            lines=(),
            subtotal="0",
            discount="0",
            shipping_cost=None,
            total_amount=None,
            delivery_type=None,
            address=None,
            payment_type=None,
            estimated_time=None,
            missing_requirements=("empty_order",),
        ),
    )
    use_case = GetOrderSummaryForConversationUseCase(service)

    summary = use_case.execute(_context())

    assert summary.missing_requirements == ("empty_order",)
    assert any(c["name"] == "get_order_summary" for c in service.calls)


def test_summary_without_an_order_is_a_business_error():
    service = FakeOrderService(current=CurrentOrderDTO(found=False))
    use_case = GetOrderSummaryForConversationUseCase(service)

    with pytest.raises(NoActiveOrderError):
        use_case.execute(_context())


def test_quote_delivery_works_without_any_order():
    delivery = FakeDeliveryService()
    order_service = FakeOrderService()
    use_case = QuoteDeliveryForConversationUseCase(delivery)
    address = AddressCommand(
        street="San Juan", street_number="3250", city="Rosario", province="Santa Fe"
    )

    result = use_case.execute(QuoteDeliveryQuery(address=address), _context())

    assert result.available is True
    assert result.shipping_cost == "350"
    # No order was read or created.
    assert order_service.calls == []
    assert delivery.calls[0][0] == "biz-1"
