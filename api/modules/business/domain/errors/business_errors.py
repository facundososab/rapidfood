"""Business domain errors."""


class BusinessDomainError(Exception):
    """Base class for all business domain errors."""


class BusinessConfigurationNotFoundError(BusinessDomainError):
    def __init__(self, business_config_id: str) -> None:
        super().__init__(
            f"BusinessConfiguration '{business_config_id}' not found."
        )


class AddressNotFoundError(BusinessDomainError):
    def __init__(self, address_id: str) -> None:
        super().__init__(f"Address '{address_id}' not found.")


class AddressDoesNotBelongToBusinessError(BusinessDomainError):
    def __init__(self, address_id: str, business_config_id: str) -> None:
        super().__init__(
            f"Address '{address_id}' does not belong to business '{business_config_id}'."
        )


class InvalidBusinessHoursError(BusinessDomainError):
    pass
