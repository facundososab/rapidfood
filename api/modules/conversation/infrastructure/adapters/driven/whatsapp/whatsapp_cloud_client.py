"""WhatsApp Cloud API client (Meta Graph API) implementing `WhatsAppSenderPort`.

Thin, injectable HTTP wrapper: a `requests.Session` (also used by the Mercado Pago
adapter) is injected so tests exercise the exact request without real network.
"""
from __future__ import annotations

import logging
from typing import Any, Sequence

import requests

from modules.conversation.application.ports.driven.whatsapp_sender import (
    WhatsAppSenderPort,
)
from modules.conversation.domain.errors import WhatsAppSendError
from modules.conversation.domain.models.whatsapp_configuration import (
    WhatsAppConfiguration,
)

logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.facebook.com"
DEFAULT_TIMEOUT = 15


class WhatsAppCloudClient(WhatsAppSenderPort):
    def __init__(
        self,
        session: Any | None = None,
        base_url: str = GRAPH_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._session = session or requests.Session()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def send_text(
        self, *, config: WhatsAppConfiguration, to: str, body: str
    ) -> None:
        self._post(
            config,
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"preview_url": False, "body": body},
            },
        )

    def send_template(
        self,
        *,
        config: WhatsAppConfiguration,
        to: str,
        template_name: str,
        language_code: str,
        body_params: Sequence[str] = (),
    ) -> None:
        template: dict = {
            "name": template_name,
            "language": {"code": language_code or "es_AR"},
        }
        if body_params:
            template["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(param)}
                        for param in body_params
                    ],
                }
            ]
        self._post(
            config,
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": template,
            },
        )

    def download_media(
        self, *, config: WhatsAppConfiguration, media_id: str
    ) -> tuple[bytes, str | None]:
        """Two-step media download: resolve the id to a URL, then fetch the bytes.

        The temporary URL expires in ~5 minutes, so this must run right away (the
        webhook does it inline). Both calls need the access token.
        """
        headers = {"Authorization": f"Bearer {config.access_token}"}
        meta_url = f"{self._base_url}/{config.api_version}/{media_id}"
        meta_response = self._session.get(
            meta_url, headers=headers, timeout=self._timeout
        )
        if meta_response.status_code >= 300:
            raise WhatsAppSendError(
                f"Media resolve failed: {_error_text(meta_response)}",
                status_code=meta_response.status_code,
            )
        meta = meta_response.json() or {}
        url = meta.get("url")
        if not url:
            raise WhatsAppSendError("Media resolve returned no URL")

        response = self._session.get(url, headers=headers, timeout=self._timeout)
        if response.status_code >= 300:
            raise WhatsAppSendError(
                f"Media download failed: {_error_text(response)}",
                status_code=response.status_code,
            )
        return response.content, meta.get("mime_type")

    def _post(self, config: WhatsAppConfiguration, payload: dict) -> None:
        url = (
            f"{self._base_url}/{config.api_version}/"
            f"{config.phone_number_id}/messages"
        )
        headers = {
            "Authorization": f"Bearer {config.access_token}",
            "Content-Type": "application/json",
        }
        response = self._session.post(
            url, json=payload, headers=headers, timeout=self._timeout
        )
        if response.status_code >= 300:
            raise WhatsAppSendError(
                _error_text(response), status_code=response.status_code
            )


def _error_text(response) -> str:
    try:
        body = response.json()
    except Exception:
        body = None
    if isinstance(body, dict):
        error = body.get("error") or {}
        message = error.get("message")
        if message:
            code = error.get("code")
            return f"WhatsApp API error {code}: {message}"
    return f"WhatsApp API returned HTTP {response.status_code}"
