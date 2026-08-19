from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DeleteClientCommand:
    client_id: str


@dataclass(frozen=True)
class DeleteClientResponse:
    id: str


class DeleteClientPort(Protocol):
    def execute(self, command: DeleteClientCommand) -> DeleteClientResponse: ...