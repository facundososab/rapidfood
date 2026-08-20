from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ClientIdentityPort(Protocol):
    def resolve_client_id(self, channel: str, channel_identity: str) -> str | None: ...


@runtime_checkable
class OrderDraftPort(Protocol):
    def find_active_draft(self, conversation_id: str): ...

    def create_draft(self, conversation_id: str, client_id: str | None = None): ...

    def confirm_draft(self, conversation_id: str, draft_id: str): ...

    def abandon_draft(self, conversation_id: str, draft_id: str): ...


@runtime_checkable
class CatalogProductQueryPort(Protocol):
    def search_products(self, query: str): ...


@runtime_checkable
class BusinessConfigurationPort(Protocol):
    def is_business_open(self, moment): ...


@runtime_checkable
class CouponValidationPort(Protocol):
    def validate_coupon(self, coupon_code: str, client_id: str | None = None): ...
