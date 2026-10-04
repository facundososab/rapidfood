"""Adapts the client module's public ports to `ClientServicePort`."""
from __future__ import annotations

import re
from typing import Any, Optional

from modules.client.application.ports.driver.create_client_ports import (
    CreateClientCommand,
)
from modules.conversation.application.ports.driven.client_service import (
    ClientInfoDTO,
    ClientServicePort,
)


def _phone_candidates(phone: str) -> list[str]:
    """Equivalent spellings of the same phone, in lookup order.

    WhatsApp sends the wa_id as bare digits ("5493413531061") while a client
    created elsewhere may be stored as "+5493413531061", "549 341 353 1061", etc.
    Matching all of these avoids creating a duplicate client for the same person.
    """
    raw = (phone or "").strip()
    digits = re.sub(r"\D", "", raw)
    candidates: list[str] = []
    for candidate in (raw, digits, f"+{digits}" if digits else ""):
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


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

    def _find_existing(self, phone: str):
        for candidate in _phone_candidates(phone):
            try:
                found = self._find_by_phone_number(candidate)
            except Exception:
                found = None
            if found is not None:
                return found
        return None

    def resolve_client(
        self, full_name: str, phone_number: Optional[str] = None
    ) -> Optional[str]:
        phone = (phone_number or "").strip()
        if not phone or self._create_client is None:
            return None

        existing = self._find_existing(phone)
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
            existing = self._find_existing(phone)
            return existing.id if existing is not None else None
