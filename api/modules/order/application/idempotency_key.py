"""Channel-neutral idempotency key derivation for order mutations.

The key must be stable across retries of the SAME logical intent and distinct
across different intents. It is derived from the business, the conversation,
the channel message, the operation name and a canonical hash of the arguments.

Canonicalization matters: the same arguments serialized with a different
property order MUST produce the same hash. ``run_id``-style tracing identifiers
MUST NOT participate (a retry produces a new run).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional


def canonical_args_hash(args: Optional[Mapping[str, Any]] = None) -> str:
    """SHA-256 over canonicalized JSON so property order does not matter."""
    payload = json.dumps(
        dict(args or {}),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_idempotency_key(
    *,
    business_config_id: str,
    conversation_id: Optional[str],
    external_message_id: str,
    operation_name: str,
    args: Optional[Mapping[str, Any]] = None,
) -> str:
    """Stable key for one logical operation on one incoming message."""
    identity = {
        "business_config_id": str(business_config_id),
        "conversation_id": str(conversation_id) if conversation_id else None,
        "external_message_id": str(external_message_id),
        "operation_name": str(operation_name),
        "args_hash": canonical_args_hash(args),
    }
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
