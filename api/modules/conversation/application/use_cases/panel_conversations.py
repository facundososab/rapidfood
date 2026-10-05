"""Panel chat use cases: list conversations, write as a human, reply as the agent.

These belong to `conversation`'s application layer: they reuse the message
persistence and the real agent flow. No business rules live here.
"""
from __future__ import annotations

from uuid import uuid4

from modules.conversation.application.ports.driven.clock import ClockPort
from modules.conversation.application.ports.driven.conversation_repository import (
    ConversationRepositoryPort,
)
from modules.conversation.application.ports.driven.message_repository import (
    MessageRepositoryPort,
)
from modules.conversation.application.ports.driver.panel_conversation_ports import (
    ClientReplyResultDTO,
    ConversationDetailDTO,
    ConversationMessageDTO,
    ConversationSummaryDTO,
)
from modules.conversation.application.ports.driver.whatsapp_messaging_ports import (
    SendConversationMessageCommand,
)
from modules.conversation.application.use_cases.handle_incoming_message import (
    HandleIncomingMessageCommand,
    HandleIncomingMessageUseCase,
)
from modules.conversation.domain.errors import ConversationNotFoundError
from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.domain.models.message import Message
from modules.conversation.domain.value_objects import (
    MessageAuthor,
    MessageRole,
    MessageStatus,
)


def _message_dto(message: Message) -> ConversationMessageDTO:
    return ConversationMessageDTO(
        message_id=message.message_id,
        role=str(message.role),
        author=str(message.author) if message.author else None,
        content=message.content,
        created_at=message.created_at.isoformat() if message.created_at else None,
    )


def _display_name(info) -> Optional[str]:
    if info is None:
        return None
    full = f"{info.name} {info.last_name}".strip()
    return full or None


def _detail(record, messages, client_info=None) -> ConversationDetailDTO:
    return ConversationDetailDTO(
        conversation_id=record.conversation_id,
        channel=record.channel,
        external_thread_id=record.external_thread_id,
        client_id=record.client_id,
        agent_paused=bool(record.agent_paused),
        messages=tuple(_message_dto(m) for m in messages),
        client_name=_display_name(client_info),
        client_phone=(client_info.phone_number if client_info else None),
        last_intent=str(record.last_intent) if record.last_intent else None,
        overall_sentiment=(
            str(record.overall_sentiment) if record.overall_sentiment else None
        ),
    )


class ListConversationsUseCase:
    def __init__(
        self,
        conversation_repository: ConversationRepositoryPort,
        message_repository: MessageRepositoryPort,
        client_service=None,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._client_service = client_service

    def _client_info(self, record):
        if self._client_service is None or not record.client_id:
            return None
        try:
            return self._client_service.get_client(record.client_id)
        except Exception:
            return None

    def execute(self) -> list[ConversationSummaryDTO]:
        summaries = []
        for record in self._conversation_repository.list_conversations():
            messages = self._message_repository.list_by_conversation(
                record.conversation_id
            )
            last = messages[-1] if messages else None
            client_info = self._client_info(record)
            summaries.append(
                ConversationSummaryDTO(
                    conversation_id=record.conversation_id,
                    channel=record.channel,
                    external_thread_id=record.external_thread_id,
                    client_id=record.client_id,
                    agent_paused=bool(record.agent_paused),
                    message_count=len(messages),
                    client_name=_display_name(client_info),
                    client_phone=(client_info.phone_number if client_info else None),
                    last_message=last.content if last else None,
                    last_role=str(last.role) if last else None,
                    last_at=(
                        last.created_at.isoformat()
                        if last and last.created_at
                        else None
                    ),
                )
            )
        summaries.sort(key=lambda s: s.last_at or "", reverse=True)
        return summaries


class GetConversationDetailUseCase:
    def __init__(
        self,
        conversation_repository: ConversationRepositoryPort,
        message_repository: MessageRepositoryPort,
        client_service=None,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._client_service = client_service

    def _client_info(self, record):
        if self._client_service is None or not record.client_id:
            return None
        try:
            return self._client_service.get_client(record.client_id)
        except Exception:
            return None

    def execute(self, conversation_id: str) -> ConversationDetailDTO:
        record = self._conversation_repository.get_by_id(conversation_id)
        if record is None:
            raise ConversationNotFoundError(conversation_id)
        messages = self._message_repository.list_by_conversation(conversation_id)
        return _detail(record, messages, self._client_info(record))


class AppendOperatorMessageUseCase:
    """A human takes the keyboard and writes as the business (no LLM)."""

    def __init__(
        self,
        conversation_repository: ConversationRepositoryPort,
        message_repository: MessageRepositoryPort,
        clock: ClockPort,
        send_message=None,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._clock = clock
        self._send_message = send_message

    def execute(self, conversation_id: str, content: str) -> ConversationDetailDTO:
        record = self._conversation_repository.get_by_id(conversation_id)
        if record is None:
            raise ConversationNotFoundError(conversation_id)

        self._message_repository.add(
            Message(
                message_id=str(uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.AGENT,
                author=MessageAuthor.OPERATOR,
                content=content,
                status=MessageStatus.PROCESSED,
                created_at=self._clock.now(),
            )
        )
        # Deliver to the customer's channel (WhatsApp) when applicable.
        if self._send_message is not None:
            self._send_message.execute(
                SendConversationMessageCommand(
                    conversation_id=conversation_id, content=content
                )
            )
        messages = self._message_repository.list_by_conversation(conversation_id)
        return _detail(record, messages)


class ReplyAsClientForConversationUseCase:
    """The operator types as the customer; the real agent answers (unless paused)."""

    def __init__(
        self,
        conversation_repository: ConversationRepositoryPort,
        message_repository: MessageRepositoryPort,
        handle_incoming_message: HandleIncomingMessageUseCase,
        clock: ClockPort,
        send_message=None,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._handle_incoming_message = handle_incoming_message
        self._clock = clock
        self._send_message = send_message

    def execute(self, conversation_id: str, content: str) -> ClientReplyResultDTO:
        record = self._conversation_repository.get_by_id(conversation_id)
        if record is None:
            raise ConversationNotFoundError(conversation_id)

        external_message_id = str(uuid4())
        context = AgentExecutionContext(
            business_configuration_id=record.business_config_id,
            conversation_id=conversation_id,
            channel=record.channel,
            client_id=record.client_id,
            external_thread_id=record.external_thread_id,
            external_message_id=external_message_id,
        )

        # The turn policy (persist USER + human-takeover pause) lives in the core
        # use case, shared with every channel driver.
        result = self._handle_incoming_message.execute(
            HandleIncomingMessageCommand(context=context, content=content)
        )
        paused = result.paused
        response = result.response or None
        # The agent's reply must reach the customer's WhatsApp, not just the panel
        # (the message is already persisted by the handler).
        if response and not paused and self._send_message is not None:
            self._send_message.execute(
                SendConversationMessageCommand(
                    conversation_id=conversation_id, content=response
                )
            )

        messages = self._message_repository.list_by_conversation(conversation_id)
        return ClientReplyResultDTO(
            conversation_id=conversation_id,
            paused=paused,
            response=response,
            detail=_detail(record, messages),
        )


class SetConversationTakeoverUseCase:
    def __init__(
        self,
        conversation_repository: ConversationRepositoryPort,
        message_repository: MessageRepositoryPort,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository

    def execute(self, conversation_id: str, paused: bool) -> ConversationDetailDTO:
        if self._conversation_repository.get_by_id(conversation_id) is None:
            raise ConversationNotFoundError(conversation_id)
        self._conversation_repository.set_agent_paused(conversation_id, paused)
        refreshed = self._conversation_repository.get_by_id(conversation_id)
        messages = self._message_repository.list_by_conversation(conversation_id)
        return _detail(refreshed, messages)
