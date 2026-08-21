from __future__ import annotations

from typing import Protocol, runtime_checkable

from modules.conversation.application.ports.driver.conversation_commands import (
    AddMessageCommand,
    GetOrCreateConversationCommand,
    ListMessagesQuery,
    ReceiveMessageCommand,
)
from modules.conversation.application.ports.driver.conversation_responses import (
    AddMessageResult,
    GetOrCreateConversationResult,
    ListMessagesResult,
    ReceiveMessageResult,
)


@runtime_checkable
class GetOrCreateConversationDriver(Protocol):
    def execute(self, command: GetOrCreateConversationCommand) -> GetOrCreateConversationResult: ...


@runtime_checkable
class AddMessageDriver(Protocol):
    def execute(self, command: AddMessageCommand) -> AddMessageResult: ...


@runtime_checkable
class ListMessagesDriver(Protocol):
    def execute(self, query: ListMessagesQuery) -> ListMessagesResult: ...


@runtime_checkable
class ReceiveMessageDriver(Protocol):
    def execute(self, command: ReceiveMessageCommand) -> ReceiveMessageResult: ...
