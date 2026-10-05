"""Pure parsing of WhatsApp Cloud API webhook payloads.

Kept framework-free and side-effect-free so it can be unit-tested with plain
dicts. Meta's payload nests everything under ``entry[].changes[].value``; status
updates (delivered/read) arrive alongside messages and are ignored here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class InboundWhatsAppMessage:
    message_id: str
    wa_id: str
    # Exactly one of these is set, depending on the WhatsApp message type.
    text: Optional[str] = None
    audio_media_id: Optional[str] = None
    audio_mime_type: Optional[str] = None

    @property
    def is_audio(self) -> bool:
        return self.audio_media_id is not None


@dataclass(frozen=True, slots=True)
class WebhookMetadata:
    phone_number_id: Optional[str] = None
    display_phone_number: Optional[str] = None


def extract_metadata(payload: Any) -> WebhookMetadata:
    """The business number that received the message (for diagnostics/routing)."""
    for value in _iter_change_values(payload):
        metadata = value.get("metadata") or {}
        phone_number_id = metadata.get("phone_number_id")
        if phone_number_id:
            return WebhookMetadata(
                phone_number_id=str(phone_number_id),
                display_phone_number=metadata.get("display_phone_number"),
            )
    return WebhookMetadata()


def extract_phone_number_id(payload: Any) -> Optional[str]:
    return extract_metadata(payload).phone_number_id


def extract_contact_name(payload: Any) -> Optional[str]:
    """The WhatsApp display name of the sender, when present."""
    for value in _iter_change_values(payload):
        for contact in value.get("contacts") or []:
            if not isinstance(contact, dict):
                continue
            profile = contact.get("profile") or {}
            name = profile.get("name")
            if name:
                return str(name).strip() or None
    return None


def parse_inbound_messages(payload: Any) -> list[InboundWhatsAppMessage]:
    """Extract text and audio messages; ignore statuses and other types."""
    messages: list[InboundWhatsAppMessage] = []
    for value in _iter_change_values(payload):
        for raw in value.get("messages") or []:
            if not isinstance(raw, dict):
                continue
            wa_id = raw.get("from")
            message_id = raw.get("id")
            if not wa_id or not message_id:
                continue
            message = _parse_message(raw, str(message_id), str(wa_id))
            if message is not None:
                messages.append(message)
    return messages


def _parse_message(raw: dict, message_id: str, wa_id: str) -> Optional[InboundWhatsAppMessage]:
    message_type = raw.get("type")
    if message_type == "text":
        text = (raw.get("text") or {}).get("body")
        if not text:
            return None
        return InboundWhatsAppMessage(
            message_id=message_id, wa_id=wa_id, text=str(text)
        )
    if message_type == "audio":
        audio = raw.get("audio") or {}
        media_id = audio.get("id")
        if not media_id:
            return None
        return InboundWhatsAppMessage(
            message_id=message_id,
            wa_id=wa_id,
            audio_media_id=str(media_id),
            audio_mime_type=audio.get("mime_type"),
        )
    return None


def _iter_change_values(payload: Any):
    if not isinstance(payload, dict):
        return
    for entry in payload.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict):
                continue
            value = change.get("value")
            if isinstance(value, dict):
                yield value
