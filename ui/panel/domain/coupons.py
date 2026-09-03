"""Derived visual state for coupons.

The schema has no `active` field. State is derived for display only and must not be
persisted:
  - Vencido    -> dateOfExpiration < now
  - Agotado    -> availableUses <= 0
  - Disponible -> not expired and has uses
"""
from __future__ import annotations

from datetime import datetime

from ..services import dtos

EXPIRED = "expired"
EXHAUSTED = "exhausted"
AVAILABLE = "available"

LABELS = {EXPIRED: "Vencido", EXHAUSTED: "Agotado", AVAILABLE: "Disponible"}


def coupon_state(coupon: dtos.Coupon, now: datetime = None) -> str:
    now = now or datetime.now()
    if coupon.dateOfExpiration is not None and coupon.dateOfExpiration < now:
        return EXPIRED
    if coupon.availableUses <= 0:
        return EXHAUSTED
    return AVAILABLE


def coupon_state_label(coupon: dtos.Coupon, now: datetime = None) -> str:
    return LABELS[coupon_state(coupon, now)]
