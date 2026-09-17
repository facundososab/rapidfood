"""List products with the text search filter."""
from modules.catalog.application.ports.driver.list_products_ports import (
    ListProductsQuery,
)
from modules.catalog.application.use_cases.list_products_use_case import (
    ListProductsUseCase,
)
from modules.catalog.domain.models.product import Product, ProductState


class FakeProductRepo:
    def __init__(self, products=None):
        self.products = products or []
        self.calls = []

    def list(self, category_id=None, state=None, search=None):
        self.calls.append({"category_id": category_id, "state": state, "search": search})
        return self.products


def _product(product_id, name, description="desc"):
    return Product(
        id=product_id,
        name=name,
        description=description,
        state=ProductState.AVAILABLE,
        category_id="cat-1",
    )


def test_search_term_is_passed_to_the_repository():
    repo = FakeProductRepo([_product("p-1", "Stacker Doble")])
    use_case = ListProductsUseCase(repo)

    use_case.execute(ListProductsQuery(search="stacker"))

    assert repo.calls == [
        {"category_id": None, "state": None, "search": "stacker"}
    ]


def test_search_combines_with_category_and_availability():
    repo = FakeProductRepo([_product("p-1", "Stacker Doble")])
    use_case = ListProductsUseCase(repo)

    use_case.execute(
        ListProductsQuery(
            category_id="cat-1", state=ProductState.AVAILABLE, search="stacker"
        )
    )

    assert repo.calls[0] == {
        "category_id": "cat-1",
        "state": ProductState.AVAILABLE,
        "search": "stacker",
    }


def test_summaries_are_returned_for_the_matching_products():
    repo = FakeProductRepo([_product("p-1", "Stacker Doble")])
    use_case = ListProductsUseCase(repo)

    result = use_case.execute(ListProductsQuery(search="stacker"))

    assert [p.id for p in result] == ["p-1"]
    assert result[0].name == "Stacker Doble"
