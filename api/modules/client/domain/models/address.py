from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Address:
    id: str
    client_id: str
    street: str
    street_number: str
    city: str
    province: str
    latitude: Decimal
    longitude: Decimal
    floor: str | None = None
    apartment: str | None = None
    postal_code: str | None = None
    delivery_instructions: str | None = None
    label: str | None = None
    is_default: bool = False

    def __post_init__(self) -> None:
        if not self.street.strip():
            raise ValueError("Street cannot be blank")
        if not self.street_number.strip():
            raise ValueError("Street number cannot be blank")

    @classmethod
    def create(
        cls,
        address_id: str,
        client_id: str,
        street: str,
        street_number: str,
        city: str,
        province: str,
        latitude: Decimal,
        longitude: Decimal,
        floor: str | None = None,
        apartment: str | None = None,
        postal_code: str | None = None,
        delivery_instructions: str | None = None,
        label: str | None = None,
        is_default: bool = False,
    ) -> Address:
        return cls(
            id=address_id,
            client_id=client_id,
            street=street.strip(),
            street_number=street_number.strip(),
            city=city.strip(),
            province=province.strip(),
            latitude=latitude,
            longitude=longitude,
            floor=floor,
            apartment=apartment,
            postal_code=postal_code,
            delivery_instructions=delivery_instructions,
            label=label,
            is_default=is_default,
        )
        
    def update(
        self,
        street: str,
        street_number: str,
        city: str,
        province: str,
        latitude: Decimal,
        longitude: Decimal,
        floor: str | None = None,
        apartment: str | None = None,
        postal_code: str | None = None,
        delivery_instructions: str | None = None,
        label: str | None = None,
    ) -> None:
        if not street.strip():
            raise ValueError("Street cannot be blank")
        if not street_number.strip():
            raise ValueError("Street number cannot be blank")
            
        self.street = street.strip()
        self.street_number = street_number.strip()
        self.city = city.strip()
        self.province = province.strip()
        self.latitude = latitude
        self.longitude = longitude
        self.floor = floor
        self.apartment = apartment
        self.postal_code = postal_code
        self.delivery_instructions = delivery_instructions
        self.label = label

    def mark_as_default(self) -> None:
        self.is_default = True

    def unmark_as_default(self) -> None:
        self.is_default = False
