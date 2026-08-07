def test_receive_message_stores_user_then_agent_and_detects_intent():
    from api.modules.conversation.application.ports.driver.conversation_commands import ReceiveMessageCommand
    from api.modules.conversation.application.use_cases.receive_message import ReceiveMessageUseCase
    from api.modules.conversation.domain.value_objects import DetectedIntent

    class ConversationRepo:
        def __init__(self):
            self.saved_last_intent = None

        def find_by_channel_identity(self, channel: str, channel_identity: str):
            return None

        def create(self, conversation):
            return conversation

        def save_last_intent(self, conversation_id: str, last_intent):
            self.saved_last_intent = (conversation_id, last_intent)

    class MessageRepo:
        def __init__(self):
            self.saved = []

        def add(self, message):
            self.saved.append(message)
            return message

        def list_by_conversation(self, conversation_id: str):
            return []

    class IntentDetector:
        def detect(self, content: str):
            return DetectedIntent.START_ORDER

    class Clock:
        def now(self):
            from datetime import datetime, timezone

            return datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    class OrderPorts:
        def __init__(self):
            self.created = 0

        def find_active_draft(self, conversation_id: str):
            return None

        def create_draft(self, conversation_id: str, client_id=None):
            self.created += 1
            return {"draft_id": "draft-1"}

        def confirm_draft(self, conversation_id: str, draft_id: str):
            raise AssertionError("should not confirm")

        def abandon_draft(self, conversation_id: str, draft_id: str):
            return None

    use_case = ReceiveMessageUseCase(
        conversation_repository=ConversationRepo(),
        message_repository=MessageRepo(),
        intent_detector=IntentDetector(),
        clock=Clock(),
        order_draft_port=OrderPorts(),
    )

    result = use_case.execute(
        ReceiveMessageCommand(channel="WHATSAPP", channel_identity="+5491112345678", content="Quiero pedir una pizza")
    )

    assert result.intent is DetectedIntent.START_ORDER
    assert result.user_message_id
    assert result.agent_message_id
    assert result.response


def test_receive_message_disambiguates_active_draft_using_order_related_ports():
    from datetime import datetime, timezone

    from api.modules.conversation.application.ports.driver.conversation_commands import ReceiveMessageCommand
    from api.modules.conversation.application.use_cases.receive_message import ReceiveMessageUseCase
    from api.modules.conversation.domain.value_objects import DetectedIntent

    class ConversationRepo:
        def find_by_channel_identity(self, channel: str, channel_identity: str):
            return None

        def create(self, conversation):
            return conversation

        def save_last_intent(self, conversation_id: str, last_intent):
            return None

    class MessageRepo:
        def add(self, message):
            return message

        def list_by_conversation(self, conversation_id: str):
            return []

    class IntentDetector:
        def detect(self, content: str):
            return DetectedIntent.START_ORDER

    class Clock:
        def now(self):
            return datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    class OrderPorts:
        def __init__(self):
            self.created = 0

        def find_active_draft(self, conversation_id: str):
            return {"draft_id": "draft-1"}

        def create_draft(self, conversation_id: str, client_id=None):
            self.created += 1
            raise AssertionError("should not create a new draft while one is active")

        def confirm_draft(self, conversation_id: str, draft_id: str):
            raise AssertionError("should not confirm during disambiguation")

        def abandon_draft(self, conversation_id: str, draft_id: str):
            return None

    class CatalogPort:
        def __init__(self):
            self.queries = []

        def search_products(self, query: str):
            self.queries.append(query)
            return ["pizza-margherita"]

    class BusinessConfigurationPort:
        def __init__(self):
            self.calls = []

        def is_business_open(self, moment):
            self.calls.append(moment)
            return True

    catalog_port = CatalogPort()
    business_configuration_port = BusinessConfigurationPort()

    use_case = ReceiveMessageUseCase(
        conversation_repository=ConversationRepo(),
        message_repository=MessageRepo(),
        intent_detector=IntentDetector(),
        clock=Clock(),
        order_draft_port=OrderPorts(),
        catalog_product_query_port=catalog_port,
        business_configuration_port=business_configuration_port,
    )

    result = use_case.execute(
        ReceiveMessageCommand(channel="WHATSAPP", channel_identity="+5491112345678", content="Quiero pedir una pizza")
    )

    assert result.intent is DetectedIntent.START_ORDER
    assert "borrador activo" in result.response.lower()
    assert catalog_port.queries == ["Quiero pedir una pizza"]
    assert len(business_configuration_port.calls) == 1


def test_receive_message_requires_explicit_confirmation_before_confirming_draft():
    from api.modules.conversation.application.ports.driver.conversation_commands import ReceiveMessageCommand
    from api.modules.conversation.application.use_cases.receive_message import ReceiveMessageUseCase
    from api.modules.conversation.domain.value_objects import DetectedIntent

    class ConversationRepo:
        def find_by_channel_identity(self, channel: str, channel_identity: str):
            return None

        def create(self, conversation):
            return conversation

        def save_last_intent(self, conversation_id: str, last_intent):
            return None

    class MessageRepo:
        def add(self, message):
            return message

        def list_by_conversation(self, conversation_id: str):
            return []

    class IntentDetector:
        def detect(self, content: str):
            return DetectedIntent.CONFIRM_ORDER

    class Clock:
        def now(self):
            from datetime import datetime, timezone

            return datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    class OrderPorts:
        def find_active_draft(self, conversation_id: str):
            return {"draft_id": "draft-1"}

        def create_draft(self, conversation_id: str, client_id=None):
            raise AssertionError("should not create")

        def confirm_draft(self, conversation_id: str, draft_id: str):
            raise AssertionError("should not confirm without explicit confirmation")

        def abandon_draft(self, conversation_id: str, draft_id: str):
            return None

    use_case = ReceiveMessageUseCase(
        conversation_repository=ConversationRepo(),
        message_repository=MessageRepo(),
        intent_detector=IntentDetector(),
        clock=Clock(),
        order_draft_port=OrderPorts(),
    )

    result = use_case.execute(
        ReceiveMessageCommand(channel="WHATSAPP", channel_identity="+5491112345678", content="dale")
    )

    assert result.intent is DetectedIntent.CONFIRM_ORDER
    assert "confirm" in result.response.lower()


def test_receive_message_confirms_active_draft_through_order_port_when_confirmation_is_explicit():
    from datetime import datetime, timezone

    from api.modules.conversation.application.ports.driver.conversation_commands import ReceiveMessageCommand
    from api.modules.conversation.application.use_cases.receive_message import ReceiveMessageUseCase
    from api.modules.conversation.domain.value_objects import DetectedIntent

    class ConversationRepo:
        def find_by_channel_identity(self, channel: str, channel_identity: str):
            return None

        def create(self, conversation):
            return conversation

        def save_last_intent(self, conversation_id: str, last_intent):
            return None

    class MessageRepo:
        def add(self, message):
            return message

        def list_by_conversation(self, conversation_id: str):
            return []

    class IntentDetector:
        def detect(self, content: str):
            return DetectedIntent.CONFIRM_ORDER

    class Clock:
        def now(self):
            return datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    class OrderPorts:
        def __init__(self):
            self.confirmed = []

        def find_active_draft(self, conversation_id: str):
            return {"draft_id": "draft-1"}

        def create_draft(self, conversation_id: str, client_id=None):
            raise AssertionError("should not create")

        def confirm_draft(self, conversation_id: str, draft_id: str):
            self.confirmed.append((conversation_id, draft_id))

        def abandon_draft(self, conversation_id: str, draft_id: str):
            return None

    class BusinessConfigurationPort:
        def __init__(self):
            self.calls = []

        def is_business_open(self, moment):
            self.calls.append(moment)
            return True

    business_configuration_port = BusinessConfigurationPort()
    order_ports = OrderPorts()

    use_case = ReceiveMessageUseCase(
        conversation_repository=ConversationRepo(),
        message_repository=MessageRepo(),
        intent_detector=IntentDetector(),
        clock=Clock(),
        order_draft_port=order_ports,
        business_configuration_port=business_configuration_port,
    )

    result = use_case.execute(
        ReceiveMessageCommand(channel="WHATSAPP", channel_identity="+5491112345678", content="dale confirmo")
    )

    assert result.intent is DetectedIntent.CONFIRM_ORDER
    assert order_ports.confirmed == [(result.conversation_id, "draft-1")]
    assert "confirm" in result.response.lower()
    assert len(business_configuration_port.calls) == 1
