from dataclasses import dataclass
from typing import List, Protocol

@dataclass(frozen=True)
class ListIngredientsResponse:
    items: List[dict]

class ListIngredientsPort(Protocol):
    def execute(self) -> ListIngredientsResponse: ...
