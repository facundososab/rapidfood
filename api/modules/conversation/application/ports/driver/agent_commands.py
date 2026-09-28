"""Driver-side commands/queries for the agent use cases.

They carry only what the model is allowed to influence. Business, conversation
and client identity always come from the trusted `AgentExecutionContext`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class SearchProductsQuery:
    query: Optional[str] = None
    category_id: Optional[str] = None
    only_available: bool = True


@dataclass(frozen=True, slots=True)
class GetProductDetailQuery:
    product_id: str


@dataclass(frozen=True, slots=True)
class AddItemCommand:
    product_variant_id: str
    quantity: int
    modifier_option_ids: tuple = ()
    removed_ingredient_ids: tuple = ()


@dataclass(frozen=True, slots=True)
class UpdateItemCommand:
    line_id: str
    quantity: Optional[int] = None
    modifier_option_ids: Optional[tuple] = None
    removed_ingredient_ids: Optional[tuple] = None


@dataclass(frozen=True, slots=True)
class RemoveItemCommand:
    line_id: str


@dataclass(frozen=True, slots=True)
class SetPaymentTypeCommand:
    payment_type: str


@dataclass(frozen=True, slots=True)
class SetClientCommand:
    name: str
    phone_number: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ApplyCouponCommand:
    coupon_code: str


@dataclass(frozen=True, slots=True)
class AddressCommand:
    """Delivery address as the customer says it: street + number are enough.

    City/province/postal code are completed from the restaurant's own address by
    the use case, so the agent does not interrogate the customer.
    """

    street: str
    street_number: str
    city: Optional[str] = None
    province: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    postal_code: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "street": self.street,
            "street_number": self.street_number,
            "floor": self.floor,
            "apartment": self.apartment,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
        }


@dataclass(frozen=True, slots=True)
class QuoteDeliveryQuery:
    address: AddressCommand


@dataclass(frozen=True, slots=True)
class SetDeliveryCommand:
    address: AddressCommand
