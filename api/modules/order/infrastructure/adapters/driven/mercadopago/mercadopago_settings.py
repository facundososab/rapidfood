import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MercadoPagoSettings:
    access_token: str
    notification_url: Optional[str] = None
    success_url: Optional[str] = None
    failure_url: Optional[str] = None
    pending_url: Optional[str] = None
    public_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    currency: str = "ARS"

    @property
    def validate_webhook_signature(self) -> bool:
        return bool(self.webhook_secret)

    @classmethod
    def from_env(cls) -> "MercadoPagoSettings":
        return cls(
            access_token=os.environ["MERCADOPAGO_ACCESS_TOKEN"],
            public_key=os.environ.get("MERCADOPAGO_PUBLIC_KEY"),
            webhook_secret=os.environ.get("MERCADOPAGO_WEBHOOK_SECRET"),
            notification_url=os.environ.get("MERCADOPAGO_NOTIFICATION_URL"),
            success_url=os.environ.get("MERCADOPAGO_SUCCESS_URL"),
            failure_url=os.environ.get("MERCADOPAGO_FAILURE_URL"),
            pending_url=os.environ.get("MERCADOPAGO_PENDING_URL"),
            currency=os.environ.get("MERCADOPAGO_CURRENCY", "ARS"),
        )
