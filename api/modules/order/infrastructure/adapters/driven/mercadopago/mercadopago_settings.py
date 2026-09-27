import os
from dataclasses import dataclass
from typing import Optional


def _env_flag(name: str) -> Optional[bool]:
    """Parse a boolean env var; ``None`` when unset/blank (use the default)."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    return raw.strip().lower() not in ("0", "false", "no", "off")


@dataclass
class MercadoPagoSettings:
    access_token: str
    notification_url: Optional[str] = None
    success_url: Optional[str] = None
    failure_url: Optional[str] = None
    pending_url: Optional[str] = None
    public_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    # Explicit switch for the webhook signature check. ``None`` derives it from
    # the presence of ``webhook_secret``; an explicit ``False`` disables the
    # check (e.g. in dev while the provider's signing key is unresolved).
    validate_signature: Optional[bool] = None
    currency: str = "ARS"
    # Checkout Pro via the Orders API (`POST /v1/orders`).
    api_base_url: str = "https://api.mercadopago.com"
    request_timeout_seconds: float = 10.0

    @property
    def validate_webhook_signature(self) -> bool:
        if self.validate_signature is not None:
            return self.validate_signature
        return bool(self.webhook_secret)

    @classmethod
    def from_env(cls) -> "MercadoPagoSettings":
        return cls(
            # Not required at boot: an empty token keeps the stack running and
            # the provider fails cleanly only when a checkout is attempted.
            access_token=os.environ.get("MERCADOPAGO_ACCESS_TOKEN", ""),
            public_key=os.environ.get("MERCADOPAGO_PUBLIC_KEY"),
            webhook_secret=os.environ.get("MERCADOPAGO_WEBHOOK_SECRET"),
            validate_signature=_env_flag("MERCADOPAGO_VALIDATE_WEBHOOK_SIGNATURE"),
            notification_url=os.environ.get("MERCADOPAGO_NOTIFICATION_URL"),
            success_url=os.environ.get("MERCADOPAGO_SUCCESS_URL"),
            failure_url=os.environ.get("MERCADOPAGO_FAILURE_URL"),
            pending_url=os.environ.get("MERCADOPAGO_PENDING_URL"),
            currency=os.environ.get("MERCADOPAGO_CURRENCY", "ARS"),
            api_base_url=os.environ.get(
                "MERCADOPAGO_API_BASE_URL", "https://api.mercadopago.com"
            ),
        )
