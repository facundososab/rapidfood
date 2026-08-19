from dataclasses import dataclass


@dataclass(frozen=True)
class Client:
    id: str
    name: str
    lastName: str
    phoneNumber: str