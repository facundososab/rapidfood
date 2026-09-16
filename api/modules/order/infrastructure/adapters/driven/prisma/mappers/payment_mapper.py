from __future__ import annotations

from modules.order.domain.models.payment import Payment
from modules.order.domain.models.payment_status import PaymentStatus


def payment_to_domain(row: object) -> Payment:  # type: ignore[type-arg]
    return Payment(
        id=str(_get(row, "id")),
        order_id=str(_get(row, "orderId", "order_id")),
        provider=str(_get(row, "provider")),
        amount=_get(row, "amount"),
        status=PaymentStatus(_enum_value(_get(row, "status"))),
        external_id=_get(row, "externalId", "external_id"),
        preference_id=_get(row, "preferenceId", "preference_id"),
        checkout_url=_get(row, "checkoutUrl", "checkout_url"),
        external_reference=_get(row, "externalReference", "external_reference"),
        expires_at=_get(row, "expiresAt", "expires_at"),
    )


def payment_to_prisma_data(payment: Payment) -> dict[str, object]:
    data: dict[str, object] = {
        "id": payment.id,
        "orderId": payment.order_id,
        "provider": payment.provider,
        "amount": payment.amount,
        "status": payment.status.value,
    }
    if payment.external_id is not None:
        data["externalId"] = payment.external_id
    if payment.preference_id is not None:
        data["preferenceId"] = payment.preference_id
    if payment.checkout_url is not None:
        data["checkoutUrl"] = payment.checkout_url
    if payment.external_reference is not None:
        data["externalReference"] = payment.external_reference
    if payment.expires_at is not None:
        data["expiresAt"] = payment.expires_at
    return data


def _get(row: object, *names: str):
    for name in names:
        if hasattr(row, name):
            return getattr(row, name)
    raise AttributeError(names[0])


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else value
