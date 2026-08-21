"""RapidfoodClient — the presentation layer's contract with the backend.

Every method returns DTOs (see dtos.py), never raw dicts. Both the in-memory mock
and the real HTTP client implement this interface, so swapping implementations does
not touch views or templates.

Nothing here is business logic: these are read/command operations the UI needs.
The authoritative rules live in the existing backend/domain.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from . import dtos


@dataclass
class Page:
    """Generic paginated result."""

    items: list
    total: int
    page: int
    page_size: int

    @property
    def num_pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.num_pages

    @property
    def page_range(self) -> range:
        return range(1, self.num_pages + 1)


@dataclass
class CouponValidation:
    valid: bool
    reason: str = ""
    coupon: Optional[dtos.Coupon] = None
    discount_amount: object = None  # Decimal when valid


class RapidfoodClient(ABC):
    # ---- Orders -----------------------------------------------------------
    @abstractmethod
    def list_orders(
        self,
        *,
        status: Optional[str] = None,
        delivery_type: Optional[str] = None,
        payment_type: Optional[str] = None,
        client_id: Optional[str] = None,
        search: Optional[str] = None,
        date_from=None,
        date_to=None,
        page: int = 1,
        page_size: int = 15,
    ) -> Page: ...

    @abstractmethod
    def get_order(self, order_id: str) -> Optional[dtos.Order]: ...

    @abstractmethod
    def update_order_status(self, order_id: str, status: str) -> dtos.Order: ...

    @abstractmethod
    def create_order(self, payload: dict) -> dtos.Order: ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> dtos.Order: ...

    @abstractmethod
    def all_orders(self) -> List[dtos.Order]: ...

    # ---- Products / categories -------------------------------------------
    @abstractmethod
    def list_products(
        self, *, search: Optional[str] = None, category_id: Optional[str] = None,
        only_available: bool = False, page: int = 1, page_size: int = 20,
    ) -> Page: ...

    @abstractmethod
    def get_product(self, product_id: str) -> Optional[dtos.Product]: ...

    @abstractmethod
    def set_product_availability(self, product_id: str, available: bool) -> dtos.Product: ...

    @abstractmethod
    def delete_product(self, product_id: str) -> None: ...

    @abstractmethod
    def save_product(self, payload: dict) -> dtos.Product: ...

    @abstractmethod
    def add_product_price(self, product_id: str, price) -> dtos.Product: ...

    @abstractmethod
    def list_categories(self) -> List[dtos.Category]: ...

    @abstractmethod
    def save_category(self, payload: dict) -> dtos.Category: ...

    # ---- Payments ---------------------------------------------------------
    @abstractmethod
    def list_payments(
        self, *, status: Optional[str] = None, provider: Optional[str] = None,
        date_from=None, date_to=None, page: int = 1, page_size: int = 15,
    ) -> Page: ...

    @abstractmethod
    def get_payment(self, payment_id: str) -> Optional[dtos.Payment]: ...

    @abstractmethod
    def all_payments(self) -> List[dtos.Payment]: ...

    # ---- Clients ----------------------------------------------------------
    @abstractmethod
    def list_clients(self, *, search: Optional[str] = None, page: int = 1, page_size: int = 15) -> Page: ...

    @abstractmethod
    def get_client(self, client_id: str) -> Optional[dtos.Client]: ...

    @abstractmethod
    def delete_client(self, client_id: str) -> None: ...

    @abstractmethod
    def create_client(self, name: str, last_name: str, phone: str) -> dtos.Client: ...

    @abstractmethod
    def search_clients(self, query: str) -> List[dtos.Client]: ...

    @abstractmethod
    def create_address(self, payload: dict) -> Optional[dtos.Address]: ...

    # ---- Coupons ----------------------------------------------------------
    @abstractmethod
    def list_coupons(self) -> List[dtos.Coupon]: ...

    @abstractmethod
    def get_coupon(self, coupon_id: str) -> Optional[dtos.Coupon]: ...

    @abstractmethod
    def get_coupon_by_code(self, code: str) -> Optional[dtos.Coupon]: ...

    @abstractmethod
    def save_coupon(self, payload: dict) -> dtos.Coupon: ...

    @abstractmethod
    def validate_coupon(self, code: str, subtotal) -> CouponValidation: ...

    @abstractmethod
    def list_applied_coupons(self, *, coupon_id: Optional[str] = None) -> List[dtos.AppliedCoupon]: ...

    # ---- Conversations ----------------------------------------------------
    @abstractmethod
    def list_conversations(self) -> List[dtos.Conversation]: ...

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[dtos.Conversation]: ...

    # ---- Business configuration ------------------------------------------
    @abstractmethod
    def get_business_config(self) -> dtos.BusinessConfiguration: ...

    @abstractmethod
    def save_business_config(self, payload: dict) -> dtos.BusinessConfiguration: ...

    # ---- Delivery configuration ------------------------------------------
    @abstractmethod
    def get_delivery_config(self, business_config_id: str) -> dict: ...

    @abstractmethod
    def save_delivery_config(self, business_config_id: str, payload: dict) -> dict: ...
