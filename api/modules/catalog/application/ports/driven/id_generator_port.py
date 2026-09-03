from typing import Protocol

class IdGeneratorPort(Protocol):
    def generate(self) -> str: ...

