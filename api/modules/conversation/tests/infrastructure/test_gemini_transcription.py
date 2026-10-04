import base64

import pytest

from modules.conversation.domain.errors import TranscriptionFailedError
from modules.conversation.infrastructure.adapters.driven.transcription.gemini_transcription_adapter import (
    GeminiTranscriptionAdapter,
)


class FakeResponse:
    def __init__(self, status_code=200, body=None, text=""):
        self.status_code = status_code
        self._body = body or {}
        self.text = text

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def post(self, url, params=None, json=None, timeout=None):
        self.calls.append({"url": url, "params": params, "json": json})
        return self._response


def _ok_body(text="Quiero una pizza"):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_transcribes_ogg_audio():
    session = FakeSession(FakeResponse(200, _ok_body("Quiero una pizza")))
    adapter = GeminiTranscriptionAdapter(
        api_key="KEY", model="gemini-3.5-flash-lite", session=session
    )

    text = adapter.transcribe(audio=b"bytes", mime_type="audio/ogg; codecs=opus")

    assert text == "Quiero una pizza"
    call = session.calls[0]
    assert call["url"].endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert call["params"] == {"key": "KEY"}
    inline = call["json"]["contents"][0]["parts"][1]["inline_data"]
    assert inline["mime_type"] == "audio/ogg"  # codecs stripped
    assert base64.b64decode(inline["data"]) == b"bytes"


def test_provider_error_raises():
    session = FakeSession(FakeResponse(400, text="bad request"))
    adapter = GeminiTranscriptionAdapter(
        api_key="KEY", model="gemini-3.5-flash-lite", session=session
    )

    with pytest.raises(TranscriptionFailedError):
        adapter.transcribe(audio=b"x", mime_type="audio/ogg")
