import pytest

from modules.conversation.domain.errors import TranscriptionFailedError
from modules.conversation.infrastructure.adapters.driven.transcription.groq_whisper_transcription_adapter import (
    GroqWhisperTranscriptionAdapter,
)


class FakeResponse:
    def __init__(self, status_code=200, text="Hola mundo"):
        self.status_code = status_code
        self.text = text


class FakeSession:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def post(self, url, headers=None, data=None, files=None, timeout=None):
        self.calls.append(
            {"url": url, "headers": headers, "data": data, "files": files}
        )
        return self._response


def test_transcribes_ogg_voice_note():
    session = FakeSession(FakeResponse(200, "Quiero una pizza"))
    adapter = GroqWhisperTranscriptionAdapter(api_key="KEY", session=session)

    text = adapter.transcribe(
        audio=b"bytes", mime_type="audio/ogg; codecs=opus"
    )

    assert text == "Quiero una pizza"
    call = session.calls[0]
    assert call["url"] == "https://api.groq.com/openai/v1/audio/transcriptions"
    assert call["headers"]["Authorization"] == "Bearer KEY"
    assert call["data"]["model"] == "whisper-large-v3-turbo"
    filename, content, mime = call["files"]["file"]
    assert filename == "audio.ogg"
    assert content == b"bytes"
    assert mime == "audio/ogg; codecs=opus"


def test_provider_error_raises():
    session = FakeSession(FakeResponse(400, "bad audio"))
    adapter = GroqWhisperTranscriptionAdapter(api_key="KEY", session=session)

    with pytest.raises(TranscriptionFailedError):
        adapter.transcribe(audio=b"x", mime_type="audio/mpeg")
