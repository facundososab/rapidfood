"""Driven port: efficient read model for the public digital menu.

The public menu is a read-only projection, so it does NOT go through the
write-oriented repositories (which fetch one product at a time and fan out into
variants/prices/ingredients/modifiers). The adapter behind this port loads the
whole menu in a CONSTANT number of queries and hands back plain read models; the
application use case only maps them to the public DTOs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Protocol, Tuple


@dataclass(frozen=True, slots=True)
class MenuReadVariant:
    id: str
    name: str
    price: Optional[Decimal]
    available: bool


@dataclass(frozen=True, slots=True)
class MenuReadModifierOption:
    id: str
    name: str
    price_delta: Decimal
    available: bool


@dataclass(frozen=True, slots=True)
class MenuReadModifierGroup:
    id: str
    name: str
    min_selections: int
    max_selections: int
    options: Tuple[MenuReadModifierOption, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MenuReadProduct:
    id: str
    name: str
    description: str
    image_url: Optional[str]
    category_id: str
    variants: Tuple[MenuReadVariant, ...] = field(default_factory=tuple)
    modifier_groups: Tuple[MenuReadModifierGroup, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MenuReadCategory:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class PublicMenuReadModel:
    categories: Tuple[MenuReadCategory, ...] = field(default_factory=tuple)
    products: Tuple[MenuReadProduct, ...] = field(default_factory=tuple)


class PublicMenuReaderPort(Protocol):
    def load_available_menu(self) -> PublicMenuReadModel: ...
