from enum import Enum


class PaymentMethod(str, Enum):
    """
    Represents the payment method chosen by the client.
    Mapped to PaymentType in DB.
    """
    CASH = "CASH"
    ONLINE = "ONLINE"
