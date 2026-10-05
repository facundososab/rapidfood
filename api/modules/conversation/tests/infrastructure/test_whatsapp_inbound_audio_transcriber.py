from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_inbound_audio_transcriber import (
    WhatsAppInboundAudioTranscriber,
)
from modules.conversation.tests.fakes import (
    FakeTranscriber,
    FakeWhatsAppMedia,
    InMemoryWhatsAppConfigurationRepository,
)


def _repo():
    repository = InMemoryWhatsAppConfigurationRepository()
    repository.upsert(
        WhatsAppConfiguration(
            business_config_id="biz-1",
            phone_number_id="123456",
            verify_token="vt",
            access_token="t",
            app_secret="s",
        )
    )
    return repository


def test_transcribes_audio():
    media = FakeWhatsAppMedia()
    transcriber = FakeTranscriber(text="Hola, quiero una pizza")
    adapter = WhatsAppInboundAudioTranscriber(_repo(), media, transcriber)

    assert (
        adapter.transcribe("123456", "wamid.aud1", "audio/ogg; codecs=opus")
        == "Hola, quiero una pizza"
    )
    assert media.calls == [("123456", "wamid.aud1")]
    assert transcriber.calls[0][0] == b"audio-bytes"


def test_returns_none_when_transcription_fails():
    adapter = WhatsAppInboundAudioTranscriber(
        _repo(), FakeWhatsAppMedia(), FakeTranscriber(error=RuntimeError("boom"))
    )
    assert adapter.transcribe("123456", "wamid.aud1") is None


def test_returns_none_when_media_download_fails():
    class BrokenMedia:
        def download_media(self, *, config, media_id):
            raise RuntimeError("no url")

    adapter = WhatsAppInboundAudioTranscriber(
        _repo(), BrokenMedia(), FakeTranscriber()
    )
    assert adapter.transcribe("123456", "wamid.aud1") is None


def test_returns_none_for_unknown_number():
    adapter = WhatsAppInboundAudioTranscriber(
        _repo(), FakeWhatsAppMedia(), FakeTranscriber()
    )
    assert adapter.transcribe("999", "wamid.aud1") is None


def test_blank_transcript_is_treated_as_none():
    adapter = WhatsAppInboundAudioTranscriber(
        _repo(), FakeWhatsAppMedia(), FakeTranscriber(text="   ")
    )
    assert adapter.transcribe("123456", "wamid.aud1") is None
