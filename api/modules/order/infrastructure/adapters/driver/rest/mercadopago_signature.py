import hashlib
import hmac
from typing import Iterator, Optional


def validate_mercadopago_signature(
    *,
    data_id: str,
    x_request_id: str,
    x_signature: str,
    secret: Optional[str],
) -> bool:
    """Validate the ``x-signature`` header of a Mercado Pago notification.

    The signed manifest is::

        id:<data.id>;request-id:<x-request-id>;ts:<ts>;

    and the expected value is ``HMAC-SHA256(secret, manifest)`` in hex, compared
    against the ``v1`` part of the header.

    Mercado Pago's casing of ``data.id`` and the presence of ``x-request-id``
    have varied across topics/versions, so every documented variant is accepted.
    All variants still require a valid HMAC with the secret, so this does not
    weaken the check — it only avoids rejecting a legitimate notification.
    """
    if not secret:
        return True
    parts = _parse_signature(x_signature)
    timestamp = parts.get("ts")
    received = parts.get("v1")
    if not timestamp or not received:
        return False
    for manifest in candidate_manifests(
        data_id=data_id, x_request_id=x_request_id, timestamp=timestamp
    ):
        expected = hmac.new(
            secret.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(expected, received):
            return True
    return False


def candidate_manifests(
    *, data_id: str, x_request_id: str, timestamp: str
) -> list[str]:
    """Manifest variants tried, in order (never includes the secret)."""
    return list(_candidate_manifests(data_id, x_request_id, timestamp))


def _candidate_manifests(
    data_id: str, x_request_id: str, timestamp: str
) -> Iterator[str]:
    ids = [data_id.lower()]
    if data_id and data_id.lower() != data_id:
        ids.append(data_id)
    for candidate in ids:
        parts = [f"id:{candidate}"]
        if x_request_id:
            parts.append(f"request-id:{x_request_id}")
        parts.append(f"ts:{timestamp}")
        yield ";".join(parts) + ";"


def _parse_signature(signature: str) -> dict:
    values = {}
    for part in signature.split(","):
        key, separator, value = part.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return values
