"""The single application entry point for an inbound channel turn.

Channel-agnostic by design: WhatsApp, LangSmith and the panel all normalize their
inbound to (context, text) and call THIS use case. It owns the turn policy —
idempotency, human takeover (pause) and the idle-session boundary — so a channel
driver can never diverge: persist USER -> (skip agent if a human took over) ->
(if the conversation went idle, close the stale order and start a fresh one) ->
run agent -> persist ASSISTANT.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driven.agent_runner import (
    AgentRunnerPort,
    AgentTurn,
)
from modules.conversation.application.ports.driven.clock import ClockPort
from modules.conversation.application.ports.driven.conversation_repository import (
    ConversationRepositoryPort,
)
from modules.conversation.application.ports.driven.message_repository import (
    MessageRepositoryPort,
)
from modules.conversation.application.ports.driven.order_service import (
    OrderServicePort,
)
from modules.conversation.domain.models.message import Message
from modules.conversation.domain.value_objects import MessageRole, MessageStatus

logger = logging.getLogger(__name__)


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


def _to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Normalize a datetime to naive UTC so aware/naive values can be compared.

    The clock returns timezone-aware UTC while timestamps read back from the DB
    are naive; comparing them directly raises. Treating a naive value as UTC is
    correct here because everything we persist is stored as UTC wall time.
    """
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


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
    # True when this inbound message was already processed (a channel retry): the
    # agent did NOT run again and the caller must not re-deliver a reply.
    already_processed: bool = False
    # True when a human took over (agent paused): the USER message was persisted
    # but the agent did not run. The caller must not deliver an agent reply.
    paused: bool = False


class HandleIncomingMessageUseCase:
    def __init__(
        self,
        message_repository: MessageRepositoryPort,
        agent_runner: AgentRunnerPort,
        clock: ClockPort,
        conversation_repository: Optional[ConversationRepositoryPort] = None,
        order_service: Optional[OrderServicePort] = None,
        session_idle_after: Optional[timedelta] = None,
        greeting_idle_after: Optional[timedelta] = None,
    ) -> None:
        self._message_repository = message_repository
        self._agent_runner = agent_runner
        self._clock = clock
        self._conversation_repository = conversation_repository
        self._order_service = order_service
        # Idle > session_idle_after starts a NEW ordering session: the previous
        # unfinished order is closed and a fresh draft is opened (silently).
        self._session_idle_after = session_idle_after
        # Idle > greeting_idle_after makes the agent greet again; a short pause
        # (minutes / couple of hours) is just a continuation of the thread.
        self._greeting_idle_after = greeting_idle_after

    def execute(
        self, command: HandleIncomingMessageCommand
    ) -> HandleIncomingMessageResult:
        context = command.context
        user_message_id = message_id_for(context)

        # Idempotency at the TURN level: Meta retries the webhook when we are slow
        # to ACK. A retry carries the SAME channel message id, which maps to the
        # same deterministic UUID. If it is already stored, do NOT run the agent
        # again (the model is non-deterministic, so a second run produces a second,
        # different reply) and do NOT persist a second assistant message.
        existing = self._message_repository.find_by_id(user_message_id)
        if existing is not None:
            return HandleIncomingMessageResult(
                conversation_id=context.conversation_id,
                user_message_id=existing.message_id,
                assistant_message_id="",
                response="",
                already_processed=True,
            )

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

        # Human takeover (single policy for EVERY channel): keep the customer
        # message so the operator sees it, but do not run the agent.
        if self._is_paused(context.conversation_id):
            return HandleIncomingMessageResult(
                conversation_id=context.conversation_id,
                user_message_id=user_message.message_id,
                assistant_message_id="",
                response="",
                paused=True,
            )

        previous = [
            message
            for message in self._message_repository.list_by_conversation(
                context.conversation_id
            )
            if message.message_id != user_message.message_id
        ]
        history = tuple((message.role, message.content) for message in previous)

        idle = self._idle_gap(previous)
        if self._starts_new_order_session(idle):
            # Internal only: never mention to the customer that a new order was
            # opened. Best-effort — an order-side failure must not break the turn.
            self._reset_idle_order(context)

        # If the agent raises, the USER message stays persisted and the error
        # propagates to the driver (a technical failure, not a business result).
        response = self._agent_runner.run(
            AgentTurn(
                message=command.content,
                context=context,
                history=history,
                new_session=self._is_new_session(previous, idle),
            )
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

    def _is_paused(self, conversation_id: str) -> bool:
        if self._conversation_repository is None:
            return False
        record = self._conversation_repository.get_by_id(conversation_id)
        return bool(record is not None and getattr(record, "agent_paused", False))

    def _idle_gap(self, previous: list[Message]) -> Optional[timedelta]:
        """Time since the last previous message, or None for the first message."""
        timestamps = [
            _to_naive_utc(getattr(message, "created_at", None))
            for message in previous
        ]
        timestamps = [ts for ts in timestamps if ts is not None]
        if not timestamps:
            return None
        now = _to_naive_utc(self._clock.now())
        if now is None:
            return None
        gap = now - max(timestamps)
        return gap if gap.total_seconds() >= 0 else timedelta(0)

    def _starts_new_order_session(self, idle: Optional[timedelta]) -> bool:
        return (
            self._order_service is not None
            and self._session_idle_after is not None
            and idle is not None
            and idle > self._session_idle_after
        )

    def _is_new_session(
        self, previous: list[Message], idle: Optional[timedelta]
    ) -> bool:
        if not previous:
            return True  # first message ever: the agent opens the conversation
        return (
            self._greeting_idle_after is not None
            and idle is not None
            and idle > self._greeting_idle_after
        )

    def _reset_idle_order(self, context: AgentExecutionContext) -> None:
        try:
            self._order_service.reset_active_order(
                context.business_configuration_id, context.conversation_id
            )
        except Exception:
            logger.exception(
                "Failed to reset the idle conversation order (conversation=%s)",
                context.conversation_id,
            )
