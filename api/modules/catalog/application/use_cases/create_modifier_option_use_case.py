from modules.catalog.application.ports.driver.create_modifier_option_ports import (
    CreateModifierOptionPort, CreateModifierOptionCommand, CreateModifierOptionResponse,
)
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.domain.models.modifier_option import ModifierOption
from modules.catalog.domain.errors.catalog_errors import ModifierGroupNotFoundError


class CreateModifierOptionUseCase(CreateModifierOptionPort):
    def __init__(
        self,
        modifier_repo: ModifierRepositoryPort,
        id_generator: IdGeneratorPort,
    ) -> None:
        self._modifier_repo = modifier_repo
        self._id_generator = id_generator

    def execute(self, command: CreateModifierOptionCommand) -> CreateModifierOptionResponse:
        group = self._modifier_repo.find_group_by_id(command.modifier_group_id)
        if group is None:
            raise ModifierGroupNotFoundError(command.modifier_group_id)

        option = ModifierOption(
            id=self._id_generator.generate(),
            modifier_group_id=command.modifier_group_id,
            name=command.name,
            price_delta=command.price_delta,
            available=True,
        )
        self._modifier_repo.save_option(option)

        return CreateModifierOptionResponse(
            id=option.id,
            modifier_group_id=option.modifier_group_id,
            name=option.name,
            price_delta=option.price_delta,
            available=option.available,
        )
