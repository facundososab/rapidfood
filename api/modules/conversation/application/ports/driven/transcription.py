"""Driven port: speech-to-text for inbound voice messages.

The channel delivers audio bytes; turning them into text is a separate provider
(Groq Whisper, Gemini, ...). The application only knows "audio in, text out".
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class TranscriptionPort(Protocol):
    def transcribe(
        self,
        *,
        audio: bytes,
        mime_type: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str: ...
