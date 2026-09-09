import hashlib
import hmac
from typing import Optional


def validate_mercadopago_signature(
    *,
    data_id: str,
    x_request_id: str,
    x_signature: str,
    secret: Optional[str],
) -> bool:
    if not secret:
        return True
    parts = _parse_signature(x_signature)
    timestamp = parts.get("ts")
    received = parts.get("v1")
    if not timestamp or not received:
        return False
    manifest_parts = []
    if data_id:
        manifest_parts.append(f"id:{data_id.lower()}")
    if x_request_id:
        manifest_parts.append(f"request-id:{x_request_id}")
    manifest_parts.append(f"ts:{timestamp}")
    manifest = ";".join(manifest_parts) + ";"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)


def _parse_signature(signature: str) -> dict:
    values = {}
    for part in signature.split(","):
        key, separator, value = part.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return values
