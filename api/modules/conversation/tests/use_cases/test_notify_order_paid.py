"""Order-paid customer notification: message composition + outbound delivery."""
from __future__ import annotations

from types import SimpleNamespace

from modules.conversation.application.ports.driver.notify_order_paid_port import (
    NotifyOrderPaidCommand,
)
from modules.conversation.application.use_cases.notify_order_paid import (
    NotifyOrderPaidUseCase,
    compose_order_paid_message,
)


class FakeConversationRepo:
    def __init__(self, record=None):
        self._record = record

    def get_by_id(self, conversation_id):
        return self._record


class FakeOutbound:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


class FakeMessageRepo:
    def __init__(self):
        self.added = []

    def add(self, message):
        self.added.append(message)
        return message


class FakeClock:
    def now(self):
        from datetime import datetime, timezone

        return datetime(2026, 10, 2, tzinfo=timezone.utc)


def _use_case(conversation_repo, outbound, message_repo=None):
    return NotifyOrderPaidUseCase(
        SimpleNamespace(get_order_summary=lambda order_id: _summary()),
        conversation_repo,
        message_repo or FakeMessageRepo(),
        outbound,
        FakeClock(),
    )


def _summary(**overrides):
    values = dict(
        order_id="o-1",
        status="PAID",
        version=3,
        lines=[
            SimpleNamespace(
                product_name="Bacon BBQ Burger",
                variant_name="Doble",
                product_variant_id="v-1",
                quantity=1,
                unit_price="10200",
                subtotal="10200",
            ),
            SimpleNamespace(
                product_name="Coca-Cola Zero",
                variant_name="500 ml",
                product_variant_id="v-2",
                quantity=1,
                unit_price="2200",
                subtotal="2200",
            ),
        ],
        subtotal="12400",
        discount="0",
        shipping_cost="2007.94",
        total_amount="14407.94",
        delivery_type="DELIVERY",
        address={
            "street": "Avenida Real",
            "street_number": "9536",
            "city": "Rosario",
        },
        payment_type="ONLINE",
        estimated_time=35,
        missing_requirements=(),
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_compose_includes_items_totals_delivery_and_eta():
    text = compose_order_paid_message(_summary())

    assert "Bacon BBQ Burger Doble" in text
    assert "Coca-Cola Zero 500 ml" in text
    assert "Total: $14407.94" in text
    assert "Envío: $2007.94" in text
    assert "Envío a domicilio" in text
    assert "Avenida Real 9536" in text
    assert "Tiempo estimado: 35 minutos" in text


def test_compose_for_pickup_has_no_address():
    text = compose_order_paid_message(
        _summary(delivery_type="PICKUP", address=None, shipping_cost=None)
    )

    assert "Retiro en el local" in text
    assert "Envío" not in text


def test_notify_sends_on_the_conversation_channel():
    repo = FakeConversationRepo(
        SimpleNamespace(
            channel="WHATSAPP",
            channel_identity="+5491112345678",
            external_thread_id="thread-1",
        )
    )
    outbound = FakeOutbound()
    use_case = _use_case(repo, outbound)

    sent = use_case.execute(
        NotifyOrderPaidCommand(conversation_id="c-1", order_id="o-1")
    )

    assert sent is True
    assert len(outbound.sent) == 1
    message = outbound.sent[0]
    assert message.conversation_id == "c-1"
    assert message.channel == "WHATSAPP"
    assert message.destination == "+5491112345678"
    assert "Total: $14407.94" in message.content


def test_notify_falls_back_to_the_external_thread_id_as_destination():
    repo = FakeConversationRepo(
        SimpleNamespace(
            channel="LANGSMITH",
            channel_identity=None,
            external_thread_id="studio-thread-1",
        )
    )
    outbound = FakeOutbound()
    use_case = _use_case(repo, outbound)

    use_case.execute(NotifyOrderPaidCommand(conversation_id="c-1", order_id="o-1"))

    assert outbound.sent[0].destination == "studio-thread-1"


def test_notify_is_a_noop_for_an_unknown_conversation():
    outbound = FakeOutbound()
    use_case = NotifyOrderPaidUseCase(
        SimpleNamespace(), FakeConversationRepo(None), FakeMessageRepo(), outbound, FakeClock()
    )

    assert (
        use_case.execute(
            NotifyOrderPaidCommand(conversation_id="missing", order_id="o-1")
        )
        is False
    )
    assert outbound.sent == []
