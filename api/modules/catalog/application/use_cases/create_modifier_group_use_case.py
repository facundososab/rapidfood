from modules.catalog.application.ports.driver.create_modifier_group_ports import (
    CreateModifierGroupPort, CreateModifierGroupCommand, CreateModifierGroupResponse,
)
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort
from modules.catalog.application.ports.driven.product_repository_port import ProductRepositoryPort
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.domain.models.modifier_group import ModifierGroup
from modules.catalog.domain.errors.catalog_errors import ProductNotFoundError


class CreateModifierGroupUseCase(CreateModifierGroupPort):
    def __init__(
        self,
        product_repo: ProductRepositoryPort,
        modifier_repo: ModifierRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._product_repo = product_repo
        self._modifier_repo = modifier_repo
        self._id_generator = id_generator

    def execute(self, command: CreateModifierGroupCommand) -> CreateModifierGroupResponse:
        product = self._product_repo.find_by_id(command.product_id)
        if product is None:
            raise ProductNotFoundError(command.product_id)

        group = ModifierGroup(
            id=self._id_generator.generate(),
            product_id=command.product_id,
            name=command.name,
            min_selections=command.min_selections,
            max_selections=command.max_selections,
        )
        self._modifier_repo.save_group(group)

        return CreateModifierGroupResponse(
            id=group.id,
            product_id=group.product_id,
            name=group.name,
            min_selections=group.min_selections,
            max_selections=group.max_selections,
        )
