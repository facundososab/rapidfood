"""Adapts the business module's configuration query to the order module's port.

Computes `is_open` from the configured weekly hours (domain service) and exposes
the real business_config_id so the delivery quote can be requested.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from modules.business.application.ports.driver.get_business_configuration_port import (
    GetBusinessConfigurationQuery,
)
from modules.order.application.ports.driven.business_config_query import (
    BusinessConfigQueryPort,
    BusinessConfigSnapshot,
)
from modules.order.domain.services.opening_hours import is_open_now

logger = logging.getLogger(__name__)


class BusinessConfigQueryAdapter(BusinessConfigQueryPort):
    def __init__(self, get_configuration: Any, business_config_id: str = "default") -> None:
        self._get_configuration = get_configuration
        self._business_config_id = business_config_id

    def get_config(self) -> BusinessConfigSnapshot:
        try:
            result = self._get_configuration.execute(
                GetBusinessConfigurationQuery(business_config_id=self._business_config_id)
            )
        except Exception as exc:  # cross-context: business errors aren't importable here
            logger.warning(
                "Business configuration unavailable (%s); using non-restrictive defaults.",
                exc,
            )
            return BusinessConfigSnapshot(
                is_open=True,
                shipping_cost=Decimal("0"),
                min_order_amount=Decimal("0"),
                business_config_id=self._business_config_id,
            )
        return BusinessConfigSnapshot(
            is_open=is_open_now(result.get("businessHours", [])),
            shipping_cost=Decimal(str(result.get("shippingCost") or 0)),
            min_order_amount=Decimal(str(result.get("minOrder") or 0)),
            business_config_id=result["id"],
        )
