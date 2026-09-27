"""Driven port: resolve a client from what the customer typed.

The channel driver would normally resolve the client from the phone number; for
Studio (where the customer types it) the agent needs the same capability. The
concrete adapter delegates to the client module's public ports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True, slots=True)
class ClientInfoDTO:
    id: str
    name: str
    last_name: str
    phone_number: str


class ClientServicePort(Protocol):
    def get_client(self, client_id: str) -> Optional[ClientInfoDTO]:
        """Display data for a known client (name/phone), or None."""
        ...

    def resolve_client(
        self, full_name: str, phone_number: Optional[str] = None
    ) -> Optional[str]:
        """Return the client id for this phone.

        Returns None when no client can be resolved or created (for example, no
        phone number, or a single-word name). The order keeps the typed name as a
        snapshot, so the flow never gets stuck.
        """
        ...
