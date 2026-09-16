from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RemoveAddressCommand:
    address_id: str
    client_id: str


class RemoveAddressPort(Protocol):
    def execute(self, command: RemoveAddressCommand) -> None: ...
