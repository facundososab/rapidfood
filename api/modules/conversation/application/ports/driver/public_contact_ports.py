"""Driver ports: public business contact profile for the digital menu."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True, slots=True)
class PublicContactView:
    business_name: Optional[str]
    whatsapp_number: Optional[str]
    whatsapp_enabled: bool


class GetPublicContactPort(Protocol):
    def execute(self, business_configuration_id: str) -> PublicContactView: ...
