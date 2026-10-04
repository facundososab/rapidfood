import hashlib
import hmac
import json

import pytest

from modules.conversation.configuration.container import build_container
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)
from modules.conversation.domain.models.conversation import Conversation
from modules.conversation.infrastructure.adapters.driver.whatsapp.payload import (
    extract_metadata,
    extract_phone_number_id,
    parse_inbound_messages,
)
from modules.conversation.tests.fakes import (
    FakeTranscriber,
    FakeWhatsAppMedia,
    FakeWhatsAppSender,
    InMemoryConversationRepository,
    InMemoryMessageRepository,
    InMemoryWhatsAppConfigurationRepository,
)

APP_SECRET = "app-secret"
PHONE_NUMBER_ID = "123456"
WA_ID = "5491100000000"


class FakeRunner:
    def run(self, turn):
        return f"eco: {turn.message}"


def _payload(text="Quiero una pizza", phone_number_id=PHONE_NUMBER_ID, message_id="wamid.ABC"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "display_phone_number": "5491100000001",
                                "phone_number_id": phone_number_id,
                            },
                            "messages": [
                                {
                                    "from": WA_ID,
                                    "id": message_id,
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def _audio_payload(media_id="wamid.AUD", phone_number_id=PHONE_NUMBER_ID, message_id="wamid.ABC"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {
                                "display_phone_number": "5491100000001",
                                "phone_number_id": phone_number_id,
                            },
                            "messages": [
                                {
                                    "from": WA_ID,
                                    "id": message_id,
                                    "type": "audio",
                                    "audio": {
                                        "id": media_id,
                                        "mime_type": "audio/ogg; codecs=opus",
                                        "voice": True,
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def _sign(raw: bytes, secret=APP_SECRET) -> str:
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.fixture
def wired(monkeypatch):
    config_repo = InMemoryWhatsAppConfigurationRepository()
    config_repo.upsert(
        WhatsAppConfiguration(
            business_config_id="biz-1",
            phone_number_id=PHONE_NUMBER_ID,
            verify_token="verify-me",
            access_token="t",
            app_secret=APP_SECRET,
        )
    )
    sender = FakeWhatsAppSender()
    conversations = InMemoryConversationRepository()
    messages = InMemoryMessageRepository()
    container = build_container(
        conversation_repository=conversations,
        message_repository=messages,
        whatsapp_config_repository=config_repo,
        whatsapp_sender=sender,
        whatsapp_outbound=True,
        agent_runner_factory=lambda _c: FakeRunner(),
    )
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.whatsapp.views.get_app_conversation_container",
        lambda: container,
    )
    return {"container": container, "sender": sender, "conversations": conversations}


# ---- payload parsing ----

def test_extract_phone_number_id():
    assert extract_phone_number_id(_payload()) == PHONE_NUMBER_ID


def test_parse_extracts_text_messages():
    messages = parse_inbound_messages(_payload(text="Hola"))
    assert len(messages) == 1
    assert messages[0].text == "Hola"
    assert messages[0].wa_id == WA_ID
    assert messages[0].message_id == "wamid.ABC"


def test_parse_ignores_statuses_and_non_text():
    payload = _payload()
    payload["entry"][0]["changes"][0]["value"]["statuses"] = [{"status": "delivered"}]
    payload["entry"][0]["changes"][0]["value"]["messages"].append(
        {"from": WA_ID, "id": "img1", "type": "image"}
    )
    messages = parse_inbound_messages(payload)
    assert [m.text for m in messages] == ["Quiero una pizza"]



# ---- webhook endpoints ----

def test_get_verification_echoes_challenge(wired):
    from django.test import Client

    response = Client().get(
        "/api/conversation/webhook/whatsapp/",
        {"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "CHALLENGE"},
    )
    assert response.status_code == 200
    assert response.content == b"CHALLENGE"


def test_get_verification_rejects_wrong_token(wired):
    from django.test import Client

    response = Client().get(
        "/api/conversation/webhook/whatsapp/",
        {"hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "C"},
    )
    assert response.status_code == 403


def test_post_runs_agent_and_sends_reply(wired):
    from django.test import Client

    raw = json.dumps(_payload(text="Quiero una pizza")).encode()
    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw),
    )

    assert response.status_code == 200
    assert wired["sender"].texts == [
        (PHONE_NUMBER_ID, WA_ID, "eco: Quiero una pizza")
    ]
    assert len(wired["conversations"].rows) == 1


def test_post_rejects_bad_signature(wired):
    from django.test import Client

    raw = json.dumps(_payload()).encode()
    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw, "wrong"),
    )
    assert response.status_code == 403
    assert wired["sender"].texts == []


def test_post_unknown_number_is_acknowledged_and_ignored(wired):
    from django.test import Client

    raw = json.dumps(_payload(phone_number_id="999")).encode()
    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw),
    )
    assert response.status_code == 200
    assert wired["sender"].texts == []
    assert wired["conversations"].rows == {}


# ---- audio ----

def _wire(monkeypatch, transcriber, runner=None, sender=None, paused=False):
    config_repo = InMemoryWhatsAppConfigurationRepository()
    config_repo.upsert(
        WhatsAppConfiguration(
            business_config_id="biz-1",
            phone_number_id=PHONE_NUMBER_ID,
            verify_token="verify-me",
            access_token="t",
            app_secret=APP_SECRET,
        )
    )
    sender = sender or FakeWhatsAppSender()
    conversations = InMemoryConversationRepository()
    messages = InMemoryMessageRepository()
    if paused:
        conversations.create(
            Conversation(
                conversation_id="conv-paused",
                channel="WHATSAPP",
                external_thread_id=WA_ID,
                business_config_id="biz-1",
                agent_paused=True,
            )
        )
    container = build_container(
        conversation_repository=conversations,
        message_repository=messages,
        whatsapp_config_repository=config_repo,
        whatsapp_sender=sender,
        whatsapp_media=FakeWhatsAppMedia(),
        transcriber=transcriber,
        whatsapp_outbound=True,
        agent_runner_factory=lambda _c: runner or FakeRunner(),
    )
    monkeypatch.setattr(
        "modules.conversation.infrastructure.adapters.driver.whatsapp.views.get_app_conversation_container",
        lambda: container,
    )
    return {"container": container, "sender": sender, "messages": messages, "transcriber": transcriber}


def test_post_transcribes_audio_and_answers(monkeypatch):
    from django.test import Client

    wired = _wire(monkeypatch, FakeTranscriber(text="Quiero una pizza"))
    raw = json.dumps(_audio_payload()).encode()

    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw),
    )

    assert response.status_code == 200
    assert wired["sender"].texts == [(PHONE_NUMBER_ID, WA_ID, "eco: Quiero una pizza")]
    assert wired["transcriber"].calls[0][0] == b"audio-bytes"


def test_audio_without_transcription_replies_with_a_fallback(monkeypatch):
    from django.test import Client

    wired = _wire(monkeypatch, FakeTranscriber(error=RuntimeError("boom")))
    raw = json.dumps(_audio_payload()).encode()

    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw),
    )

    assert response.status_code == 200
    assert len(wired["sender"].texts) == 1
    sent_to, sent_body = wired["sender"].texts[0][1], wired["sender"].texts[0][2]
    assert sent_to == WA_ID
    assert "audio" in sent_body.lower()
    assert any(m.content == "[audio]" for m in wired["messages"].messages)


def test_agent_failure_sends_a_generic_fallback(monkeypatch):
    from django.test import Client

    class BoomRunner:
        def run(self, turn):
            raise RuntimeError("agent exploded")

    wired = _wire(monkeypatch, FakeTranscriber(), runner=BoomRunner())
    raw = json.dumps(_payload()).encode()

    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw),
    )

    assert response.status_code == 200
    assert len(wired["sender"].texts) == 1
    assert "procesar" in wired["sender"].texts[0][2].lower()


def test_delivery_failure_does_not_break_the_webhook(monkeypatch):
    from django.test import Client

    class RaisingSender:
        def send_text(self, *, config, to, body):
            raise RuntimeError("131030 recipient not in allowed list")

        def send_template(self, **kwargs):
            raise RuntimeError("nope")

    wired = _wire(monkeypatch, FakeTranscriber(), sender=RaisingSender())
    raw = json.dumps(_payload()).encode()

    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw),
    )

    assert response.status_code == 200
    # The turn is persisted in the panel even though delivery failed.
    assert len(wired["messages"].messages) >= 1


def test_extract_metadata_reports_display_number():
    metadata = extract_metadata(_payload())
    assert metadata.phone_number_id == PHONE_NUMBER_ID
    assert metadata.display_phone_number == "5491100000001"


def test_extract_contact_name():
    from modules.conversation.infrastructure.adapters.driver.whatsapp.payload import (
        extract_contact_name,
    )

    payload = _payload()
    payload["entry"][0]["changes"][0]["value"]["contacts"] = [
        {"profile": {"name": "Facundo Sosa"}, "wa_id": WA_ID}
    ]
    assert extract_contact_name(payload) == "Facundo Sosa"
    assert extract_contact_name(_payload()) is None


def test_paused_conversation_does_not_run_the_agent(monkeypatch):
    from django.test import Client

    wired = _wire(monkeypatch, FakeTranscriber(), paused=True)
    raw = json.dumps(_payload(text="Hola, quiero un pedido")).encode()

    response = Client().post(
        "/api/conversation/webhook/whatsapp/",
        data=raw,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=_sign(raw),
    )

    assert response.status_code == 200
    # The agent must stay silent while a human owns the conversation.
    assert wired["sender"].texts == []
    # The inbound is still stored so the operator sees it in the panel.
    assert any(m.content == "Hola, quiero un pedido" for m in wired["messages"].messages)
