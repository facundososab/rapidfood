from enum import Enum


class OrderOrigin(str, Enum):
    """
    Where the order originated: POS/mostrador (IN_PLACE) or an agent (AGENT).
    Mapped to OrderOrigin in DB.
    """
    IN_PLACE = "IN_PLACE"
    AGENT = "AGENT"