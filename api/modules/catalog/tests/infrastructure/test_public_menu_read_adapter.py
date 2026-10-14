"""Prisma public menu read adapter: constant queries and live price resolution.

Uses a fake Prisma client (no database): the adapter is pure mapping plus a fixed
number of ``find_many`` calls.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

from modules.catalog.infrastructure.adapters.driven.prisma.public_menu_read_adapter import (
    PrismaPublicMenuReadAdapter,
)


class FakeClient:
    def __init__(self, *, categories, products, prices, options):
        self.calls = {"category": 0, "product": 0, "price": 0, "modifieroption": 0}
        self.category_query = None
        self.product_query = None
        self.price_query = None
        self.option_query = None

        outer = self

        class _Collection:
            def __init__(self, name, rows):
                self.name = name
                self.rows = rows

            def find_many(self, **kwargs):
                outer.calls[self.name] += 1
                setattr(outer, f"{self.name}_query", kwargs)
                return self.rows

        self.category = _Collection("category", categories)
        self.product = _Collection("product", products)
        self.price = _Collection("price", prices)
        self.modifieroption = _Collection("modifieroption", options)


def _variant(variant_id, name="Simple", available=True):
    return SimpleNamespace(id=variant_id, name=name, available=available)


def _group(group_id, name="Agregados", min_selections=0, max_selections=3):
    return SimpleNamespace(
        id=group_id,
        name=name,
        minSelections=min_selections,
        maxSelections=max_selections,
    )


def _product(product_id, category_id, variants=(), groups=()):
    return SimpleNamespace(
        id=product_id,
        name=f"Product {product_id}",
        description="desc",
        imageUrl=None,
        categoryId=category_id,
        variants=list(variants),
        modifierGroups=list(groups),
    )


def test_maps_products_variants_and_modifier_options():
    client = FakeClient(
        categories=[SimpleNamespace(id="cat-1", description="Bebidas")],
        products=[
            _product(
                "p-1",
                "cat-1",
                variants=[_variant("v-1", "Grande")],
                groups=[_group("g-1")],
            )
        ],
        prices=[
            SimpleNamespace(
                productVariantId="v-1", sinceDate=datetime(2026, 1, 1), price=Decimal("150.00")
            )
        ],
        options=[
            SimpleNamespace(
                id="o-1",
                modifierGroupId="g-1",
                name="Extra queso",
                priceDelta=Decimal("50.00"),
                available=False,
            )
        ],
    )

    model = PrismaPublicMenuReadAdapter(client).load_available_menu()

    assert model.categories[0].id == "cat-1"
    assert model.categories[0].name == "Bebidas"
    product = model.products[0]
    assert product.id == "p-1"
    assert product.variants[0].price == Decimal("150.00")
    group = product.modifier_groups[0]
    assert group.options[0].name == "Extra queso"
    assert group.options[0].price_delta == Decimal("50.00")
    assert group.options[0].available is False


def test_only_available_products_and_current_price_are_used():
    today = date.today()
    client = FakeClient(
        categories=[],
        products=[
            _product(
                "p-1",
                "cat-1",
                variants=[_variant("v-1")],
            )
        ],
        prices=[
            SimpleNamespace(
                productVariantId="v-1",
                sinceDate=datetime(today.year, 1, 1),
                price=Decimal("100.00"),
            ),
        ],
        options=[],
    )

    model = PrismaPublicMenuReadAdapter(client).load_available_menu()

    # Product query filters to available only, with nested relations included.
    assert client.product_query["where"] == {"available": True}
    assert client.product_query["include"] == {
        "variants": True,
        "modifierGroups": True,
    }
    # Price window ends today so a future price is never shown.
    assert client.price_query["where"]["sinceDate"]["lte"].date() == today
    assert model.products[0].variants[0].price == Decimal("100.00")


def test_loads_the_menu_in_a_constant_number_of_queries():
    """No per-product fan-out: exactly one query per collection."""
    client = FakeClient(
        categories=[SimpleNamespace(id="cat-1", description="Bebidas")],
        products=[
            _product(
                f"p-{i}",
                "cat-1",
                variants=[_variant(f"v-{i}")],
                groups=[_group(f"g-{i}")],
            )
            for i in range(10)
        ],
        prices=[
            SimpleNamespace(
                productVariantId=f"v-{i}",
                sinceDate=datetime(2026, 1, 1),
                price=Decimal("10.00"),
            )
            for i in range(10)
        ],
        options=[],
    )

    PrismaPublicMenuReadAdapter(client).load_available_menu()

    assert client.calls == {
        "category": 1,
        "product": 1,
        "price": 1,
        "modifieroption": 1,
    }


def test_empty_catalog_skips_the_child_queries():
    client = FakeClient(categories=[], products=[], prices=[], options=[])

    model = PrismaPublicMenuReadAdapter(client).load_available_menu()

    assert model.categories == ()
    assert model.products == ()
    # No variant/group ids -> no redundant price/option queries.
    assert client.calls["price"] == 0
    assert client.calls["modifieroption"] == 0
