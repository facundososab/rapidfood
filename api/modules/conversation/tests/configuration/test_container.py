def test_container_explicitly_wires_use_cases():
    from api.modules.conversation.configuration.container import build_container

    container = build_container()

    assert container.get_or_create_conversation_use_case is not None
    assert container.add_message_use_case is not None
    assert container.list_messages_use_case is not None
    assert container.receive_message_use_case is not None
