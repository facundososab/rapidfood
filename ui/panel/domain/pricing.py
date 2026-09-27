"""Presentation-side price derivation.

Current price = the Price with the greatest sinceDate that is <= now. There is no
Product.currentPrice field in the schema; this is a derived (calculated) value.

Products are priced per variant, so the product-level price list is usually
empty. When that happens the effective price is derived from the variant prices
already present in the product payload (the list endpoint includes variants), so
list views do not need a detail request per product.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from ..services import dtos


def _valid_product_prices(product: dtos.Product, now: datetime) -> list:
    return [p for p in (product.prices or []) if p.sinceDate <= now]


def _variant_prices(product: dtos.Product) -> list:
    return [
        v.currentPrice
        for v in (product.variants or [])
        if v.available and v.currentPrice is not None
    ]


def current_price(product: dtos.Product, now: Optional[datetime] = None) -> Optional[Decimal]:
    if product is None:
        return None
    now = now or datetime.now()

    valid = _valid_product_prices(product, now)
    if valid:
        return max(valid, key=lambda p: p.sinceDate).price

    variant_prices = _variant_prices(product)
    if variant_prices:
        return min(variant_prices)
    return None


def has_variable_price(product: dtos.Product, now: Optional[datetime] = None) -> bool:
    """True when the effective price comes from the variant prices.

    The customer must pick a variant, so the UI should present it as "varies".
    """
    if product is None:
        return False
    now = now or datetime.now()
    if _valid_product_prices(product, now):
        return False
    return bool(_variant_prices(product))


def price_history(product: dtos.Product):
    return sorted(product.prices, key=lambda p: p.sinceDate, reverse=True)
