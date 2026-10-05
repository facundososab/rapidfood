import pytest

from modules.conversation.domain.errors import WhatsAppSendError
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)
from modules.conversation.infrastructure.adapters.driven.whatsapp.whatsapp_cloud_client import (
    WhatsAppCloudClient,
)


class FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self._response


def _config():
    return WhatsAppConfiguration(
        business_config_id="biz-1",
        phone_number_id="123456",
        verify_token="vt",
        access_token="TOKEN",
        app_secret="secret",
        api_version="v21.0",
    )


def test_send_text_builds_the_graph_request():
    session = FakeSession(FakeResponse(200, {"messages": [{"id": "wamid.1"}]}))
    client = WhatsAppCloudClient(session=session)

    client.send_text(config=_config(), to="5491100000000", body="Hola!")

    call = session.calls[0]
    assert call["url"] == "https://graph.facebook.com/v21.0/123456/messages"
    assert call["headers"]["Authorization"] == "Bearer TOKEN"
    assert call["json"] == {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "5491100000000",
        "type": "text",
        "text": {"preview_url": False, "body": "Hola!"},
    }


def test_send_template_includes_body_params():
    session = FakeSession(FakeResponse(200, {}))
    client = WhatsAppCloudClient(session=session)

    client.send_template(
        config=_config(),
        to="5491100000000",
        template_name="order_paid",
        language_code="es_AR",
        body_params=("Pedido #12",),
    )

    template = session.calls[0]["json"]["template"]
    assert template["name"] == "order_paid"
    assert template["language"] == {"code": "es_AR"}
    assert template["components"][0]["parameters"][0]["text"] == "Pedido #12"


def test_api_error_raises_with_provider_message():
    session = FakeSession(
        FakeResponse(400, {"error": {"code": 131047, "message": "Re-engagement"}})
    )
    client = WhatsAppCloudClient(session=session)

    with pytest.raises(WhatsAppSendError) as excinfo:
        client.send_text(config=_config(), to="x", body="y")

    assert excinfo.value.status_code == 400
    assert "131047" in str(excinfo.value)
