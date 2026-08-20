from typing import List

from modules.catalog.application.ports.driver.list_categories_ports import (
    ListCategoriesPort,
)
from modules.catalog.application.ports.driven.category_repository_port import (
    CategoryRepositoryPort,
)
from modules.catalog.domain.models.category import Category


class ListCategoriesUseCase(ListCategoriesPort):
    def __init__(self, categories: CategoryRepositoryPort) -> None:
        self._categories = categories

    def execute(self) -> List[Category]:
        return list(self._categories.list())