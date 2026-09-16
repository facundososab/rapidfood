from modules.catalog.application.ports.driver.delete_modifier_group_ports import (
    DeleteModifierGroupPort,
    DeleteModifierGroupCommand,
    DeleteModifierGroupResponse,
)
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort
from modules.catalog.domain.errors.catalog_errors import ModifierGroupNotFoundError


class DeleteModifierGroupUseCase(DeleteModifierGroupPort):
    def __init__(self, modifier_repo: ModifierRepositoryPort) -> None:
        self._modifier_repo = modifier_repo

    def execute(self, command: DeleteModifierGroupCommand) -> DeleteModifierGroupResponse:
        group = self._modifier_repo.find_group_by_id(command.group_id)
        if group is None:
            raise ModifierGroupNotFoundError(command.group_id)

        self._modifier_repo.delete_group(command.group_id)
        return DeleteModifierGroupResponse(id=command.group_id)
