"""Retry the remote cancellation of a superseded checkout, independently.

The local order mutation already committed; the remote cancellation is
best-effort and may have failed (timeout/5xx). This use case reuses the SAME
provider idempotency key, so it can never cancel a different logical checkout,
and it does NOT touch the order.
"""
from __future__ import annotations

from modules.order.application.idempotency_key import build_idempotency_key
from modules.order.application.ports.driven.payment_provider import (
    CancelCheckoutRequest,
    PaymentProviderError,
    PaymentProviderPort,
)
from modules.order.application.ports.driven.payment_repository import (
    PaymentAttemptRepository,
)
from modules.order.application.ports.driver.payment_ports import (
    CancelSupersededCheckoutCommand,
    CancelSupersededCheckoutPort,
    CancelSupersededCheckoutResult,
)
from modules.order.domain.errors.order_errors import (
    OrderStateError,
    PaymentAttemptNotFoundError,
)
from modules.order.domain.models.cancellation_status import CancellationStatus


class CancelSupersededCheckoutUseCase(CancelSupersededCheckoutPort):
    def __init__(
        self,
        payment_repo: PaymentAttemptRepository,
        payment_provider: PaymentProviderPort,
    ) -> None:
        self._payment_repo = payment_repo
        self._payment_provider = payment_provider

    def execute(
        self, command: CancelSupersededCheckoutCommand
    ) -> CancelSupersededCheckoutResult:
        attempt = self._payment_repo.get_by_id(command.payment_attempt_id)
        if attempt is None:
            raise PaymentAttemptNotFoundError(
                f"Payment attempt {command.payment_attempt_id} not found"
            )
        if not attempt.superseded:
            raise OrderStateError("Only a superseded attempt can be cancelled remotely")

        if not attempt.external_id:
            # Nothing was ever sent to the provider.
            attempt.cancellation_status = CancellationStatus.NOT_REQUIRED
            self._payment_repo.save(attempt)
            return CancelSupersededCheckoutResult(
                payment_attempt_id=attempt.id,
                cancellation_status=CancellationStatus.NOT_REQUIRED.value,
                already_cancelled=False,
            )

        key = attempt.cancel_idempotency_key or build_idempotency_key(
            business_config_id=attempt.id,
            conversation_id=None,
            external_message_id=f"cancel:{attempt.id}",
            operation_name="cancel_payment_checkout",
            args={"attempt_id": attempt.id, "external_id": attempt.external_id},
        )
        if attempt.cancel_idempotency_key != key:
            attempt.cancel_idempotency_key = key
            self._payment_repo.save(attempt)

        try:
            provider_result = self._payment_provider.cancel_checkout(
                CancelCheckoutRequest(
                    external_id=attempt.external_id,
                    idempotency_key=key,
                )
            )
        except PaymentProviderError:
            # Local consistency does not depend on this; retry later.
            attempt.mark_cancellation_failed()
            self._payment_repo.save(attempt)
            return CancelSupersededCheckoutResult(
                payment_attempt_id=attempt.id,
                cancellation_status=CancellationStatus.FAILED.value,
                already_cancelled=False,
            )

        if provider_result.already_cancelled:
            attempt.mark_remote_already_cancelled()
        else:
            attempt.mark_remote_cancelled()
        saved = self._payment_repo.save(attempt)

        return CancelSupersededCheckoutResult(
            payment_attempt_id=saved.id,
            cancellation_status=saved.cancellation_status.value,
            already_cancelled=provider_result.already_cancelled,
        )
