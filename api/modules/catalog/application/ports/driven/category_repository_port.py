from typing import Protocol
from modules.catalog.domain.models.category import Category



class CategoryRepositoryPort(Protocol):
    def save(self, category: Category) -> None: ...

    def find_by_id(self, category_id: str) -> Category | None: ...

    def list(self) -> list[Category]: ...


    