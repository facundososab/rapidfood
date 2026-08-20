class ClientError(Exception):
    """Error base para el dominio de clientes."""

class ClientNotFoundError(ClientError):
    def __init__(self, client_id: str) -> None:
        super().__init__(f"No existe un cliente con id {client_id}")
        self.client_id = client_id