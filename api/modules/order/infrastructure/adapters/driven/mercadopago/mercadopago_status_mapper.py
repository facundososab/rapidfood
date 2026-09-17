from modules.order.domain.models.payment_status import PaymentStatus


def map_mercadopago_status(status: str) -> PaymentStatus:
    """Map a Mercado Pago status (payment or order) to the domain status.

    Orders API uses ``created``/``action_required`` for an open checkout and
    ``canceled`` for a cancelled one; Payments API uses ``pending``/``in_process``
    and ``cancelled``. Unknown values fail closed.
    """
    return {
        "approved": PaymentStatus.APPROVED,
        "rejected": PaymentStatus.REJECTED,
        "cancelled": PaymentStatus.FAILED,
        "canceled": PaymentStatus.FAILED,
        "refunded": PaymentStatus.FAILED,
        "charged_back": PaymentStatus.FAILED,
        "expired": PaymentStatus.EXPIRED,
        "pending": PaymentStatus.PENDING,
        "in_process": PaymentStatus.PENDING,
        "created": PaymentStatus.PENDING,
        "action_required": PaymentStatus.PENDING,
    }.get(status, PaymentStatus.FAILED)
