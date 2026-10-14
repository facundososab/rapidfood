from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, Tuple


@dataclass(frozen=True, slots=True)
class PublicVariant:
    id: str
    name: str
    price: Optional[str]
    available: bool


@dataclass(frozen=True, slots=True)
class PublicModifierOption:
    id: str
    name: str
    price_delta: str
    available: bool


@dataclass(frozen=True, slots=True)
class PublicModifierGroup:
    id: str
    name: str
    min_selections: int
    max_selections: int
    options: Tuple[PublicModifierOption, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class PublicProduct:
    id: str
    name: str
    description: str
    image_url: Optional[str]
    variants: Tuple[PublicVariant, ...] = field(default_factory=tuple)
    modifier_groups: Tuple[PublicModifierGroup, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class PublicCategory:
    id: str
    name: str
    products: Tuple[PublicProduct, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class PublicMenu:
    categories: Tuple[PublicCategory, ...] = field(default_factory=tuple)


class GetPublicMenuPort(Protocol):
    def execute(self) -> PublicMenu: ...
