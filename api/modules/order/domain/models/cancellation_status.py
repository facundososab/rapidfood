"""Local lifecycle of a remote checkout cancellation.

Kept separate from the provider status: an attempt can be superseded locally
while its remote cancellation is still pending or has failed, and that remote
cancellation must be retryable on its own without repeating the order mutation.
"""
from enum import Enum


class CancellationStatus(str, Enum):
    # The attempt was never sent to the provider, or superseding it required no
    # remote cancellation (e.g. no checkout was created yet).
    NOT_REQUIRED = "NOT_REQUIRED"
    # Superseded locally; the remote cancellation has not been attempted yet.
    PENDING = "PENDING"
    # The provider cancelled the checkout.
    CANCELLED = "CANCELLED"
    # The provider reported it was already cancelled (idempotent success).
    REMOTE_ALREADY_CANCELLED = "REMOTE_ALREADY_CANCELLED"
    # The remote cancellation failed (timeout/5xx); retry independently.
    FAILED = "FAILED"

    def is_open(self) -> bool:
        """Still needs a remote cancellation attempt."""
        return self in {CancellationStatus.PENDING, CancellationStatus.FAILED}
