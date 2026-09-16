from modules.catalog.application.ports.driver.set_variant_ingredients_ports import (
    SetVariantIngredientsPort,
    SetVariantIngredientsCommand,
    SetVariantIngredientsResponse,
    VariantIngredientItem,
)
from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort
from modules.catalog.application.ports.driven.ingredient_repository_port import IngredientRepositoryPort
from modules.catalog.application.ports.driven.variant_ingredient_repository_port import VariantIngredientRepositoryPort
from modules.catalog.domain.errors.catalog_errors import VariantNotFoundError, IngredientNotFoundError


class SetVariantIngredientsUseCase(SetVariantIngredientsPort):
    def __init__(
        self,
        variant_repo: VariantRepositoryPort,
        ingredient_repo: IngredientRepositoryPort,
        variant_ingredient_repo: VariantIngredientRepositoryPort,
    ) -> None:
        self._variant_repo = variant_repo
        self._ingredient_repo = ingredient_repo
        self._variant_ingredient_repo = variant_ingredient_repo

    def execute(self, command: SetVariantIngredientsCommand) -> SetVariantIngredientsResponse:
        variant = self._variant_repo.find_by_id(command.variant_id)
        if variant is None:
            raise VariantNotFoundError(command.variant_id)

        # Validate all ingredients exist
        for entry in command.entries:
            if self._ingredient_repo.find_by_id(entry.ingredient_id) is None:
                raise IngredientNotFoundError(entry.ingredient_id)

        entries_dicts = [
            {"ingredient_id": e.ingredient_id, "removable": e.removable}
            for e in command.entries
        ]
        result = self._variant_ingredient_repo.set_ingredients(command.variant_id, entries_dicts)

        return SetVariantIngredientsResponse(
            variant_id=command.variant_id,
            ingredients=[
                VariantIngredientItem(
                    id=vi.id,
                    ingredient_id=vi.ingredient_id,
                    name=vi.ingredient_name,
                    removable=vi.removable,
                )
                for vi in result
            ],
        )
