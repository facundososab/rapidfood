from typing import List, Protocol

from modules.catalog.domain.models.category import Category


class ListCategoriesPort(Protocol):
    def execute(self) -> List[Category]: ...