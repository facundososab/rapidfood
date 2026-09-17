"""Derived visual state for coupons.

State is derived for display only and must not be persisted:
  - Pausado    -> isActive is False (administrative pause)
  - Vencido    -> dateOfExpiration < now
  - Agotado    -> availableUses <= 0 (when the counter is limited)
  - Disponible -> active, not expired and has uses left
"""
from __future__ import annotations

from datetime import datetime

from ..services import dtos

PAUSED = "paused"
EXPIRED = "expired"
EXHAUSTED = "exhausted"
AVAILABLE = "available"

LABELS = {PAUSED: "Pausado", EXPIRED: "Vencido", EXHAUSTED: "Agotado", AVAILABLE: "Disponible"}


def coupon_state(coupon: dtos.Coupon, now: datetime = None) -> str:
    now = now or datetime.now()
    if not getattr(coupon, "isActive", True):
        return PAUSED
    if coupon.dateOfExpiration is not None and coupon.dateOfExpiration < now:
        return EXPIRED
    if coupon.availableUses is not None and coupon.availableUses <= 0:
        return EXHAUSTED
    return AVAILABLE


def coupon_state_label(coupon: dtos.Coupon, now: datetime = None) -> str:
    return LABELS[coupon_state(coupon, now)]
