"""Groq Whisper speech-to-text (OpenAI-compatible transcription endpoint).

Chosen because WhatsApp voice notes are OGG/Opus and Groq Whisper accepts that
container directly (no ffmpeg conversion), and because Groq is already a
configured LLM provider in this project.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from modules.conversation.application.ports.driven.transcription import (
    TranscriptionPort,
)
from modules.conversation.domain.errors import TranscriptionFailedError

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "whisper-large-v3-turbo"
DEFAULT_TIMEOUT = 60

_EXTENSIONS = {
    "audio/ogg": "ogg",
    "audio/opus": "ogg",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/webm": "webm",
    "audio/flac": "flac",
    "audio/aac": "aac",
    "audio/amr": "amr",
}


def _filename_for(mime_type: Optional[str]) -> str:
    base = (mime_type or "").split(";")[0].strip().lower()
    return f"audio.{_EXTENSIONS.get(base, 'ogg')}"


class GroqWhisperTranscriptionAdapter(TranscriptionPort):
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        session: Any | None = None,
        base_url: str = GROQ_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._session = session or requests.Session()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def transcribe(
        self,
        *,
        audio: bytes,
        mime_type: Optional[str] = None,
        language: Optional[str] = None,
    ) -> str:
        data: dict[str, str] = {"model": self._model, "response_format": "text"}
        if language:
            data["language"] = language
        files = {
            "file": (
                _filename_for(mime_type),
                audio,
                mime_type or "application/octet-stream",
            )
        }
        response = self._session.post(
            f"{self._base_url}/audio/transcriptions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            data=data,
            files=files,
            timeout=self._timeout,
        )
        if response.status_code >= 300:
            raise TranscriptionFailedError(
                f"Groq transcription failed (HTTP {response.status_code}): "
                f"{response.text[:200]}"
            )
        return (response.text or "").strip()
