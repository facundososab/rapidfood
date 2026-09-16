from modules.catalog.application.ports.driver.delete_modifier_option_ports import (
    DeleteModifierOptionPort,
    DeleteModifierOptionCommand,
    DeleteModifierOptionResponse,
)
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort
from modules.catalog.domain.errors.catalog_errors import ModifierOptionNotFoundError


class DeleteModifierOptionUseCase(DeleteModifierOptionPort):
    def __init__(self, modifier_repo: ModifierRepositoryPort) -> None:
        self._modifier_repo = modifier_repo

    def execute(self, command: DeleteModifierOptionCommand) -> DeleteModifierOptionResponse:
        option = self._modifier_repo.find_option_by_id(command.option_id)
        if option is None:
            raise ModifierOptionNotFoundError(command.option_id)

        self._modifier_repo.delete_option(command.option_id)
        return DeleteModifierOptionResponse(id=command.option_id)
