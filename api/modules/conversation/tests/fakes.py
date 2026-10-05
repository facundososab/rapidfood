"""In-memory repositories for conversation tests (no DB)."""
from __future__ import annotations

from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.domain.value_objects import ConversationRecord


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str, str], Conversation] = {}

    def find_by_thread(self, business_config_id, channel, external_thread_id):
        return self.rows.get((business_config_id, channel, external_thread_id))

    def get_by_id(self, conversation_id):
        for conversation in self.rows.values():
            if conversation.conversation_id == conversation_id:
                return conversation
        return None

    def list_conversations(self):
        return list(self.rows.values())

    def set_agent_paused(self, conversation_id, paused):
        conversation = self.get_by_id(conversation_id)
        if conversation is not None:
            conversation.agent_paused = bool(paused)

    def set_client_id(self, conversation_id, client_id):
        conversation = self.get_by_id(conversation_id)
        if conversation is not None:
            conversation.client_id = client_id

    def find_by_channel_identity(self, channel, channel_identity):
        for conversation in self.rows.values():
            if conversation.channel == channel and conversation.client_id is None:
                return conversation
        return None

    def create(self, conversation: Conversation):
        self.rows[
            (
                conversation.business_config_id,
                conversation.channel,
                conversation.external_thread_id,
            )
        ] = conversation
        return conversation

    def save_last_intent(self, conversation_id, last_intent):
        for conversation in self.rows.values():
            if conversation.conversation_id == conversation_id:
                conversation.last_intent = last_intent


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self.messages: list = []

    def add(self, message):
        existing = self.find_by_id(message.message_id)
        if existing is not None:
            return existing
        self.messages.append(message)
        return message

    def find_by_id(self, message_id):
        for message in self.messages:
            if message.message_id == message_id:
                return message
        return None

    def list_by_conversation(self, conversation_id):
        return [m for m in self.messages if m.conversation_id == conversation_id]


class InMemoryWhatsAppConfigurationRepository:
    def __init__(self) -> None:
        self.rows: dict[str, object] = {}

    def get_by_business_config_id(self, business_config_id):
        return self.rows.get(business_config_id)

    def get_by_phone_number_id(self, phone_number_id):
        for config in self.rows.values():
            if config.phone_number_id == phone_number_id:
                return config
        return None

    def list_active(self):
        return [config for config in self.rows.values() if config.is_active]

    def upsert(self, config):
        if not config.id:
            config.id = f"cfg-{config.business_config_id}"
        self.rows[config.business_config_id] = config
        return config


class FakeWhatsAppSender:
    def __init__(self) -> None:
        self.texts: list = []
        self.templates: list = []

    def send_text(self, *, config, to, body):
        self.texts.append((config.phone_number_id, to, body))

    def send_template(self, *, config, to, template_name, language_code, body_params=()):
        self.templates.append(
            (config.phone_number_id, to, template_name, language_code, tuple(body_params))
        )


class FakeWhatsAppMedia:
    def __init__(self, content: bytes = b"audio-bytes", mime_type="audio/ogg; codecs=opus"):
        self.content = content
        self.mime_type = mime_type
        self.calls: list = []

    def download_media(self, *, config, media_id):
        self.calls.append((config.phone_number_id, media_id))
        return self.content, self.mime_type


class FakeTranscriber:
    def __init__(self, text="Quiero una pizza", error: Exception | None = None):
        self.text = text
        self.error = error
        self.calls: list = []

    def transcribe(self, *, audio, mime_type=None, language=None):
        self.calls.append((audio, mime_type, language))
        if self.error is not None:
            raise self.error
        return self.text

