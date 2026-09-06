from __future__ import annotations

from dataclasses import dataclass, field

from modules.catalog.domain.errors.catalog_errors import InvalidModifierGroupError


@dataclass
class ModifierGroup:
    id: str
    product_id: str
    name: str
    min_selections: int
    max_selections: int
    options: list = field(default_factory=list)  # list[ModifierOption]

    def __post_init__(self) -> None:
        if self.min_selections < 0:
            raise InvalidModifierGroupError("min_selections must be >= 0")
        if self.max_selections < 1:
            raise InvalidModifierGroupError("max_selections must be >= 1")
        if self.max_selections < self.min_selections:
            raise InvalidModifierGroupError("max_selections must be >= min_selections")
