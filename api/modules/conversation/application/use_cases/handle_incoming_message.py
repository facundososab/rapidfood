"""Incoming message flow: resolve -> persist USER -> agent -> persist ASSISTANT.

The conversation history is persisted in the conversation module (never in
LangSmith). The USER message is persisted BEFORE running the agent, so a failing
agent never loses what the customer said.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driven.agent_runner import (
    AgentRunnerPort,
    AgentTurn,
)
from modules.conversation.application.ports.driven.clock import ClockPort
from modules.conversation.application.ports.driven.message_repository import (
    MessageRepositoryPort,
)
from modules.conversation.domain.models.message import Message
from modules.conversation.domain.value_objects import MessageRole, MessageStatus


def message_id_for(context: AgentExecutionContext) -> str:
    """A stable, valid UUID for the incoming message.

    The Message primary key is a UUID column, and the channel message id may be
    any string (a WhatsApp id, a Studio id). A valid UUID is used as-is;
    otherwise a deterministic UUIDv5 is derived so the SAME ingress message maps
    to the SAME id across retries (message-level idempotency).
    """
    external = context.external_message_id
    if not external:
        return str(uuid4())
    try:
        return str(UUID(str(external)))
    except (ValueError, AttributeError, TypeError):
        return str(uuid5(NAMESPACE_URL, f"{context.conversation_id}:{external}"))


@dataclass(frozen=True, slots=True)
class HandleIncomingMessageCommand:
    context: AgentExecutionContext
    content: str


@dataclass(frozen=True, slots=True)
class HandleIncomingMessageResult:
    conversation_id: str
    user_message_id: str
    assistant_message_id: str
    response: str


class HandleIncomingMessageUseCase:
    def __init__(
        self,
        message_repository: MessageRepositoryPort,
        agent_runner: AgentRunnerPort,
        clock: ClockPort,
    ) -> None:
        self._message_repository = message_repository
        self._agent_runner = agent_runner
        self._clock = clock

    def execute(
        self, command: HandleIncomingMessageCommand
    ) -> HandleIncomingMessageResult:
        context = command.context
        user_message_id = message_id_for(context)

        user_message = self._message_repository.add(
            Message(
                message_id=user_message_id,
                conversation_id=context.conversation_id,
                role=MessageRole.USER,
                content=command.content,
                status=MessageStatus.RECEIVED,
                created_at=self._clock.now(),
            )
        )

        history = tuple(
            (message.role, message.content)
            for message in self._message_repository.list_by_conversation(
                context.conversation_id
            )
            if message.message_id != user_message.message_id
        )

        # If the agent raises, the USER message stays persisted and the error
        # propagates to the driver (a technical failure, not a business result).
        response = self._agent_runner.run(
            AgentTurn(message=command.content, context=context, history=history)
        )

        assistant_message = self._message_repository.add(
            Message(
                message_id=str(uuid4()),
                conversation_id=context.conversation_id,
                role=MessageRole.AGENT,
                content=response,
                status=MessageStatus.PROCESSED,
                created_at=self._clock.now(),
            )
        )

        return HandleIncomingMessageResult(
            conversation_id=context.conversation_id,
            user_message_id=user_message.message_id,
            assistant_message_id=assistant_message.message_id,
            response=response,
        )
