from modules.catalog.application.ports.driver.create_ingredient_ports import (
    CreateIngredientPort, CreateIngredientCommand, CreateIngredientResponse,
)
from modules.catalog.application.ports.driven.ingredient_repository_port import IngredientRepositoryPort
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.domain.models.ingredient import Ingredient


class CreateIngredientUseCase(CreateIngredientPort):
    def __init__(
        self,
        ingredient_repo: IngredientRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._ingredient_repo = ingredient_repo
        self._id_generator = id_generator

    def execute(self, command: CreateIngredientCommand) -> CreateIngredientResponse:
        ingredient = Ingredient(
            id=self._id_generator.generate(),
            name=command.name,
        )
        self._ingredient_repo.save(ingredient)
        return CreateIngredientResponse(id=ingredient.id, name=ingredient.name)
