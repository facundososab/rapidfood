"""Adapts the client module's public ports to `ClientServicePort`."""
from __future__ import annotations

from typing import Any, Optional

from modules.client.application.ports.driver.create_client_ports import (
    CreateClientCommand,
)
from modules.conversation.application.ports.driven.client_service import (
    ClientServicePort,
)


class ClientServiceAdapter(ClientServicePort):
    def __init__(self, find_by_phone_number: Any, create_client: Any) -> None:
        self._find_by_phone_number = find_by_phone_number
        self._create_client = create_client

    def resolve_client(
        self, full_name: str, phone_number: Optional[str] = None
    ) -> Optional[str]:
        phone = (phone_number or "").strip()
        if not phone:
            return None

        try:
            existing = self._find_by_phone_number(phone)
        except Exception:
            existing = None
        if existing is not None:
            return existing.id

        # The client module requires a non-blank last name, so a single-word name
        # cannot create a client record. The order still keeps the typed name.
        name, _, last_name = (full_name or "").strip().partition(" ")
        if not name or not last_name.strip():
            return None

        try:
            created = self._create_client.execute(
                CreateClientCommand(
                    name=name,
                    last_name=last_name.strip(),
                    phone_number=phone,
                )
            )
            return created.id
        except Exception:
            # Already created by a concurrent turn: reuse it if it exists now.
            try:
                existing = self._find_by_phone_number(phone)
            except Exception:
                existing = None
            return existing.id if existing is not None else None
