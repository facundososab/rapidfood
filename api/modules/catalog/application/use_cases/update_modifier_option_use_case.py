from modules.catalog.application.ports.driver.update_modifier_option_ports import (
    UpdateModifierOptionPort, UpdateModifierOptionCommand, UpdateModifierOptionResponse,
)
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort
from modules.catalog.domain.errors.catalog_errors import ModifierOptionNotFoundError


class UpdateModifierOptionUseCase(UpdateModifierOptionPort):
    def __init__(self, modifier_repo: ModifierRepositoryPort) -> None:
        self._modifier_repo = modifier_repo

    def execute(self, command: UpdateModifierOptionCommand) -> UpdateModifierOptionResponse:
        option = self._modifier_repo.find_option_by_id(command.option_id)
        if option is None:
            raise ModifierOptionNotFoundError(command.option_id)

        if command.name is not None:
            option.name = command.name
        if command.price_delta is not None:
            option.price_delta = command.price_delta
        if command.available is not None:
            option.available = command.available

        self._modifier_repo.save_option(option)

        return UpdateModifierOptionResponse(
            id=option.id,
            name=option.name,
            price_delta=option.price_delta,
            available=option.available,
        )
