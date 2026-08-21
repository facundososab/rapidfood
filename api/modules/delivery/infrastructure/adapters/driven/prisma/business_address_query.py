"""BusinessAddressQuery — Prisma-backed driven adapter.

Implements BusinessAddressQueryPort. Reads the Address table to verify
that an address exists and belongs to the expected business configuration.
"""

from __future__ import annotations

import logging
from typing import Optional

from prisma import Prisma

from modules.delivery.application.ports.driven.business_address_query_port import (
    AddressSnapshot,
    BusinessAddressQueryPort,
)

logger = logging.getLogger(__name__)


class BusinessAddressQuery(BusinessAddressQueryPort):
    """Reads address ownership data from Prisma."""

    def __init__(self, db: Prisma) -> None:
        self._db = db

    def get_by_id(self, address_id: str) -> Optional[AddressSnapshot]:
        """Return address ownership snapshot, or None if not found."""
        row = self._db.address.find_unique(
            where={"id": address_id}
        )
        if row is None:
            logger.debug("Address not found: %s", address_id)
            return None
        return AddressSnapshot(
            address_id=row.id,
            business_config_id=row.businessConfigId,
        )
