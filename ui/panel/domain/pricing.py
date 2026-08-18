"""Presentation-side price derivation.

Current price = the Price with the greatest sinceDate that is <= now. There is no
Product.currentPrice field in the schema; this is a derived (calculated) value.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from ..services import dtos


def current_price(product: dtos.Product, now: Optional[datetime] = None) -> Optional[Decimal]:
    now = now or datetime.now()
    valid = [p for p in product.prices if p.sinceDate <= now]
    if not valid:
        return None
    return max(valid, key=lambda p: p.sinceDate).price


def price_history(product: dtos.Product):
    return sorted(product.prices, key=lambda p: p.sinceDate, reverse=True)
