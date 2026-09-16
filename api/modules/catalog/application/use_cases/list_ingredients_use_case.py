from typing import List
from modules.catalog.application.ports.driven.ingredient_repository_port import IngredientRepositoryPort


class ListIngredientsUseCase:
    def __init__(self, ingredient_repo: IngredientRepositoryPort) -> None:
        self._ingredient_repo = ingredient_repo

    def execute(self) -> List[dict]:
        ingredients = self._ingredient_repo.list_all()
        return [{"id": i.id, "name": i.name} for i in ingredients]
