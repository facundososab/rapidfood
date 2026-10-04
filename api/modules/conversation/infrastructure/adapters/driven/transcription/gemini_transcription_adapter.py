"""Gemini speech-to-text (native audio understanding).

Used when the project is configured with Gemini (GEMINI_API_KEY). Gemini accepts
WhatsApp's OGG/Opus voice notes directly, so no audio conversion is needed.
"""
from __future__ import annotations

import base64
import logging
from typing import Any, Optional

import requests

from modules.conversation.application.ports.driven.transcription import (
    TranscriptionPort,
)
from modules.conversation.domain.errors import TranscriptionFailedError

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_TIMEOUT = 60

PROMPT = (
    "Transcribí el siguiente audio. Devolvé únicamente el texto transcripto, "
    "en el idioma original del audio, sin comentarios, sin comillas y sin "
    "agregar nada más."
)


def _normalize_mime(mime_type: Optional[str]) -> str:
    # WhatsApp sends "audio/ogg; codecs=opus"; Gemini expects the base type.
    base = (mime_type or "audio/ogg").split(";")[0].strip()
    return base or "audio/ogg"


def _extract_text(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return "".join(
        part.get("text", "") for part in parts if isinstance(part, dict)
    ).strip()


class GeminiTranscriptionAdapter(TranscriptionPort):
    def __init__(
        self,
        api_key: str,
        model: str,
        session: Any | None = None,
        base_url: str = GEMINI_BASE_URL,
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
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": PROMPT},
                        {
                            "inline_data": {
                                "mime_type": _normalize_mime(mime_type),
                                "data": base64.b64encode(audio).decode("ascii"),
                            }
                        },
                    ]
                }
            ]
        }
        url = f"{self._base_url}/models/{self._model}:generateContent"
        response = self._session.post(
            url, params={"key": self._api_key}, json=payload, timeout=self._timeout
        )
        if response.status_code >= 300:
            raise TranscriptionFailedError(
                f"Gemini transcription failed (HTTP {response.status_code}): "
                f"{response.text[:200]}"
            )
        return _extract_text(response.json())
