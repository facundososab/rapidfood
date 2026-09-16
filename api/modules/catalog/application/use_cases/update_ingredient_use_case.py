from modules.catalog.application.ports.driver.update_ingredient_ports import (
    UpdateIngredientPort, UpdateIngredientCommand, UpdateIngredientResponse,
)
from modules.catalog.application.ports.driven.ingredient_repository_port import IngredientRepositoryPort
from modules.catalog.domain.errors.catalog_errors import IngredientNotFoundError


class UpdateIngredientUseCase(UpdateIngredientPort):
    def __init__(self, ingredient_repo: IngredientRepositoryPort) -> None:
        self._ingredient_repo = ingredient_repo

    def execute(self, command: UpdateIngredientCommand) -> UpdateIngredientResponse:
        ingredient = self._ingredient_repo.find_by_id(command.ingredient_id)
        if ingredient is None:
            raise IngredientNotFoundError(command.ingredient_id)
        ingredient.name = command.name
        self._ingredient_repo.save(ingredient)
        return UpdateIngredientResponse(id=ingredient.id, name=ingredient.name)
