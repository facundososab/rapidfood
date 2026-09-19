"""Adapts the client module's public ports to `ClientServicePort`."""
from __future__ import annotations

from typing import Any, Optional

from modules.client.application.ports.driver.create_client_ports import (
    CreateClientCommand,
)
from modules.conversation.application.ports.driven.client_service import (
    ClientInfoDTO,
    ClientServicePort,
)


class ClientServiceAdapter(ClientServicePort):
    def __init__(
        self, find_by_phone_number: Any, create_client: Any, find_by_id: Any = None
    ) -> None:
        self._find_by_phone_number = find_by_phone_number
        self._create_client = create_client
        self._find_by_id = find_by_id

    def get_client(self, client_id: str) -> Optional[ClientInfoDTO]:
        try:
            found = self._find_by_id(client_id)
        except Exception:
            found = None
        if found is None:
            return None
        return ClientInfoDTO(
            id=found.id,
            name=found.name,
            last_name=found.last_name,
            phone_number=found.phone_number,
        )

    def resolve_client(
        self, full_name: str, phone_number: Optional[str] = None
    ) -> Optional[str]:
        phone = (phone_number or "").strip()
        if not phone or self._create_client is None:
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
