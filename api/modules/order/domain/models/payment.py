from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from modules.order.domain.models.payment_status import PaymentStatus


@dataclass
class Payment:
    id: str
    order_id: str
    provider: str
    amount: Decimal
    status: PaymentStatus
    external_id: Optional[str] = None
    preference_id: Optional[str] = None
    checkout_url: Optional[str] = None
    external_reference: Optional[str] = None
    expires_at: Optional[datetime] = None

    def has_same_final_status(self, status: PaymentStatus) -> bool:
        return self.status == status and status.is_final()
