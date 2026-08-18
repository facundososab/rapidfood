from abc import ABC, abstractmethod


class ClientQuery(ABC):
    """
    Driven port to fetch client information from the client module.
    """
    
    @abstractmethod
    def check_client_exists(self, client_id: str) -> bool:
        """Checks if a client exists."""
        pass
