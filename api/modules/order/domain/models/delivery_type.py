from enum import Enum


class DeliveryType(str, Enum):
    """
    Represents how the order will be delivered to the client.
    """
    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"
