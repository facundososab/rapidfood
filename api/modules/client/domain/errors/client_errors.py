class ClientError(Exception):
    """Error base para el dominio de clientes."""


class ClientDomainError(ClientError):
    pass


class ClientNotFoundError(ClientDomainError):
    def __init__(self, client_id: str) -> None:
        super().__init__(f"Client '{client_id}' not found")
        self.client_id = client_id


class ClientAlreadyExistsError(ClientDomainError):
    def __init__(self, phone_number: str) -> None:
        super().__init__(f"A client with phone '{phone_number}' already exists")
        self.phone_number = phone_number


class AddressNotFoundError(ClientDomainError):
    def __init__(self, address_id: str) -> None:
        super().__init__(f"Address '{address_id}' not found")
        self.address_id = address_id


class AddressNotOwnedByClientError(ClientDomainError):
    pass
