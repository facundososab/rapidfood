"""Driven port: catalog capabilities the agent needs.

Conversation-owned DTOs only: no Prisma models and no catalog internals cross
this boundary. The concrete adapter delegates to the catalog module's public
query ports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, Tuple


@dataclass(frozen=True, slots=True)
class ProductVariantPriceDTO:
    """Light variant projection used by search: name + price, so the agent can
    answer "how much is it?" without a second call."""

    id: str
    name: str
    price: Optional[str]
    available: bool


@dataclass(frozen=True, slots=True)
class ProductSummaryDTO:
    id: str
    name: str
    description: str
    available: bool
    category_id: Optional[str] = None
    variants: Tuple[ProductVariantPriceDTO, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class IngredientDTO:
    id: str
    name: str
    removable: bool


@dataclass(frozen=True, slots=True)
class ModifierOptionDTO:
    id: str
    name: str
    price_delta: str
    available: bool


@dataclass(frozen=True, slots=True)
class ModifierGroupDTO:
    id: str
    name: str
    min_selections: int
    max_selections: int
    options: Tuple[ModifierOptionDTO, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class VariantDTO:
    id: str
    name: str
    current_price: Optional[str]
    available: bool
    ingredients: Tuple[IngredientDTO, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ProductDetailDTO:
    id: str
    name: str
    description: str
    available: bool
    variants: Tuple[VariantDTO, ...] = field(default_factory=tuple)
    modifier_groups: Tuple[ModifierGroupDTO, ...] = field(default_factory=tuple)


class CatalogServicePort(Protocol):
    def search_products(
        self,
        business_configuration_id: str,
        query: Optional[str] = None,
        category_id: Optional[str] = None,
        only_available: bool = True,
    ) -> list[ProductSummaryDTO]: ...

    def get_product_detail(
        self, business_configuration_id: str, product_id: str
    ) -> Optional[ProductDetailDTO]: ...
