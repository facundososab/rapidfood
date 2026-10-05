"""Driver port: authenticate an inbound WhatsApp webhook.

Channel-security boundary. The adapter behind it owns the credentials and never
exposes them: the driver only learns "is this subscription token valid?", "which
business does this phone_number_id belong to?", and "is this signature valid?".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True, slots=True)
class WhatsAppWebhookIdentity:
    """A safe reference to the business behind a phone_number_id (no secrets)."""

    business_config_id: str
    phone_number_id: str
    display_phone_number: Optional[str] = None


class WhatsAppWebhookAuthenticatorPort(Protocol):
    def verify_subscription(self, token: str) -> bool: ...

    def resolve_identity(
        self, phone_number_id: str
    ) -> Optional[WhatsAppWebhookIdentity]: ...

    def verify_signature(
        self, phone_number_id: str, raw_body: bytes, signature_header: str
    ) -> bool: ...
