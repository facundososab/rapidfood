from modules.order.domain.models.payment_status import PaymentStatus


def map_mercadopago_status(status: str) -> PaymentStatus:
    return {
        "approved": PaymentStatus.APPROVED,
        "rejected": PaymentStatus.REJECTED,
        "cancelled": PaymentStatus.FAILED,
        "refunded": PaymentStatus.FAILED,
        "charged_back": PaymentStatus.FAILED,
        "expired": PaymentStatus.EXPIRED,
        "pending": PaymentStatus.PENDING,
        "in_process": PaymentStatus.PENDING,
    }.get(status, PaymentStatus.FAILED)
