from __future__ import annotations

from typing import Optional

from modules.order.domain.models.cancellation_status import CancellationStatus
from modules.order.domain.models.payment_attempt import PaymentAttempt
from modules.order.domain.models.payment_status import PaymentStatus


def payment_attempt_to_domain(row: object) -> PaymentAttempt:  # type: ignore[type-arg]
    return PaymentAttempt(
        id=str(_get(row, "id")),
        order_id=str(_get(row, "orderId", "order_id")),
        provider=str(_get(row, "provider")),
        amount=_get(row, "amount"),
        status=PaymentStatus(_enum_value(_get(row, "status"))),
        order_version=_get(row, "orderVersion", "order_version"),
        external_id=_get(row, "externalId", "external_id"),
        preference_id=_get(row, "preferenceId", "preference_id"),
        checkout_url=_get(row, "checkoutUrl", "checkout_url"),
        external_reference=_get(row, "externalReference", "external_reference"),
        expires_at=_get(row, "expiresAt", "expires_at"),
        superseded_at=_get(row, "supersededAt", "superseded_at"),
        cancellation_status=_optional_cancellation_status(
            _get(row, "cancellationStatus", "cancellation_status")
        ),
        create_idempotency_key=_get(row, "createIdempotencyKey", "create_idempotency_key"),
        cancel_idempotency_key=_get(row, "cancelIdempotencyKey", "cancel_idempotency_key"),
    )


def payment_attempt_to_prisma_data(attempt: PaymentAttempt) -> dict[str, object]:
    data: dict[str, object] = {
        "id": attempt.id,
        "orderId": attempt.order_id,
        "provider": attempt.provider,
        "amount": attempt.amount,
        "status": attempt.status.value,
    }
    optional = {
        "orderVersion": attempt.order_version,
        "externalId": attempt.external_id,
        "preferenceId": attempt.preference_id,
        "checkoutUrl": attempt.checkout_url,
        "externalReference": attempt.external_reference,
        "expiresAt": attempt.expires_at,
        "supersededAt": attempt.superseded_at,
        "cancellationStatus": (
            attempt.cancellation_status.value
            if isinstance(attempt.cancellation_status, CancellationStatus)
            else attempt.cancellation_status
        ),
        "createIdempotencyKey": attempt.create_idempotency_key,
        "cancelIdempotencyKey": attempt.cancel_idempotency_key,
    }
    for key, value in optional.items():
        if value is not None:
            data[key] = value
    return data


def _get(row: object, *names: str):
    for name in names:
        if hasattr(row, name):
            return getattr(row, name)
    raise AttributeError(names[0])


def _optional_cancellation_status(value) -> Optional[CancellationStatus]:
    if value is None:
        return None
    if isinstance(value, CancellationStatus):
        return value
    return CancellationStatus(_enum_value(value))


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else value
