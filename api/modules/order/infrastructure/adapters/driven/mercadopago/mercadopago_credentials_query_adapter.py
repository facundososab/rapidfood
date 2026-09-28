"""Adapts the Mercado Pago linkage query to the order module's driven port.

Cross-context by design: the payment flow must never break because the linkage
data is unavailable, so any failure degrades to ``None`` and the caller falls
back to the globally configured token.
"""

from __future__ import annotations

import logging
from typing import Any

from modules.mercadopago.application.ports.driver.get_mercadopago_access_token_port import (
    GetMercadoPagoAccessTokenQuery,
)
from modules.order.application.ports.driven.payment_credentials_query import (
    PaymentCredentialsQuery,
)

logger = logging.getLogger(__name__)


class MercadoPagoCredentialsQueryAdapter(PaymentCredentialsQuery):
    def __init__(self, get_access_token: Any) -> None:
        self._get_access_token = get_access_token

    def get_access_token(self, business_config_id: str) -> str | None:
        try:
            return self._get_access_token.execute(
                GetMercadoPagoAccessTokenQuery(
                    business_config_id=business_config_id
                )
            )
        except Exception as exc:  # cross-context: mercadopago errors aren't importable here
            logger.warning(
                "Mercado Pago credentials unavailable for business %s (%s); "
                "falling back to the configured token.",
                business_config_id,
                exc,
            )
            return None
