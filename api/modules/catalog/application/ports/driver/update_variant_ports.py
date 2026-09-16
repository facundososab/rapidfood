from dataclasses import dataclass
from typing import Optional, Protocol

@dataclass(frozen=True)
class UpdateVariantCommand:
    variant_id: str
    name: Optional[str] = None
    available: Optional[bool] = None

@dataclass(frozen=True)
class UpdateVariantResponse:
    id: str
    name: str
    available: bool

class UpdateVariantPort(Protocol):
    def execute(self, command: UpdateVariantCommand) -> UpdateVariantResponse: ...
