"""Public (unauthenticated) read service for the customer-facing digital menu.

The panel's shared ``RapidfoodClient`` carries the operator's Supabase token; the
public carta must never leak it. This module talks to the backend with plain
``requests`` (fresh call, no Authorization header) and degrades to empty values
on any failure so the page always renders.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings


@dataclass(frozen=True)
class PublicVariant:
    id: str
    name: str
    price: Optional[str]
    available: bool


@dataclass(frozen=True)
class PublicModifierOption:
    id: str
    name: str
    price_delta: Optional[str]
    available: bool


@dataclass(frozen=True)
class PublicModifierGroup:
    id: str
    name: str
    options: tuple


@dataclass(frozen=True)
class PublicProduct:
    id: str
    name: str
    description: str
    image_url: Optional[str]
    variants: tuple
    modifier_groups: tuple


@dataclass(frozen=True)
class PublicCategory:
    id: str
    name: str
    products: tuple


@dataclass(frozen=True)
class PublicMenu:
    categories: tuple


@dataclass(frozen=True)
class PublicContact:
    business_name: Optional[str]
    whatsapp_number: Optional[str]
    whatsapp_enabled: bool


def _get_json(path: str) -> dict:
    """GET the backend path with a fresh, unauthenticated call; degrade to {}."""
    base_url = getattr(settings, "RAPIDFOOD_API_BASE_URL", "") or ""
    if not base_url:
        return {}
    url = base_url.rstrip("/") + path
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def get_public_menu() -> PublicMenu:
    data = _get_json("/api/catalog/menu/")
    categories = tuple(
        PublicCategory(
            id=str(cat.get("id", "")),
            name=str(cat.get("name", "")),
            products=tuple(
                PublicProduct(
                    id=str(prod.get("id", "")),
                    name=str(prod.get("name", "")),
                    description=str(prod.get("description", "") or ""),
                    image_url=prod.get("image_url"),
                    variants=tuple(
                        PublicVariant(
                            id=str(var.get("id", "")),
                            name=str(var.get("name", "")),
                            price=var.get("price"),
                            available=bool(var.get("available", False)),
                        )
                        for var in (prod.get("variants") or [])
                    ),
                    modifier_groups=tuple(
                        PublicModifierGroup(
                            id=str(grp.get("id", "")),
                            name=str(grp.get("name", "")),
                            options=tuple(
                                PublicModifierOption(
                                    id=str(opt.get("id", "")),
                                    name=str(opt.get("name", "")),
                                    price_delta=opt.get("price_delta"),
                                    available=bool(opt.get("available", False)),
                                )
                                for opt in (grp.get("options") or [])
                            ),
                        )
                        for grp in (prod.get("modifier_groups") or [])
                    ),
                )
                for prod in (cat.get("products") or [])
            ),
        )
        for cat in (data.get("categories") or [])
    )
    return PublicMenu(categories=categories)


def get_public_contact() -> PublicContact:
    data = _get_json("/api/conversation/public-contact/")
    return PublicContact(
        business_name=data.get("business_name"),
        whatsapp_number=data.get("whatsapp_number"),
        whatsapp_enabled=bool(data.get("whatsapp_enabled", False)),
    )
