from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientInfo:
    """Minimal client data the order can embed in its responses."""

    id: str
    name: str
    last_name: str = ""
    phone_number: str = ""


class ClientQuery(ABC):
    """
    Driven port to fetch client information from the client module.
    """

    @abstractmethod
    def check_client_exists(self, client_id: str) -> bool:
        """Checks if a client exists."""
        pass

    @abstractmethod
    def get_client(self, client_id: str) -> Optional[ClientInfo]:
        """Returns minimal client data, or None when the client does not exist."""
        pass
