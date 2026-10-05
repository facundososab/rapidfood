"""Domain errors of the Mercado Pago linkage context.

These errors never carry HTTP semantics: the REST driver adapter translates
them into status codes.
"""


class MercadoPagoError(Exception):
    """Base error for the Mercado Pago linkage domain."""


class MercadoPagoConfigurationError(MercadoPagoError):
    """The OAuth application settings are incomplete or invalid.

    Raised when the module cannot build a redirect URL or exchange a code
    because ``MERCADOPAGO_CLIENT_ID`` / ``MERCADOPAGO_CLIENT_SECRET`` /
    ``MERCADOPAGO_REDIRECT_URI`` are not configured.
    """


class MercadoPagoStateError(MercadoPagoError):
    """The OAuth ``state`` is tampered with, malformed or expired."""


class MercadoPagoNotLinkedError(MercadoPagoError):
    """A business that must have a linked Mercado Pago account does not have one.

    Reserved for operations that require an active link (for example, charging
    with the business credentials). Reading the link status does not raise it.
    """

    def __init__(self, business_config_id: str) -> None:
        super().__init__(
            f"Business '{business_config_id}' has no linked Mercado Pago account"
        )
        self.business_config_id = business_config_id


class MercadoPagoOAuthError(MercadoPagoError):
    """Mercado Pago rejected the OAuth token exchange or could not be reached."""
