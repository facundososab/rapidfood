from modules.catalog.application.ports.driver.update_modifier_group_ports import (
    UpdateModifierGroupPort, UpdateModifierGroupCommand, UpdateModifierGroupResponse,
)
from modules.catalog.application.ports.driven.modifier_repository_port import ModifierRepositoryPort
from modules.catalog.domain.errors.catalog_errors import ModifierGroupNotFoundError


class UpdateModifierGroupUseCase(UpdateModifierGroupPort):
    def __init__(self, modifier_repo: ModifierRepositoryPort) -> None:
        self._modifier_repo = modifier_repo

    def execute(self, command: UpdateModifierGroupCommand) -> UpdateModifierGroupResponse:
        group = self._modifier_repo.find_group_by_id(command.group_id)
        if group is None:
            raise ModifierGroupNotFoundError(command.group_id)

        if command.name is not None:
            group.name = command.name
        if command.min_selections is not None:
            group.min_selections = command.min_selections
        if command.max_selections is not None:
            group.max_selections = command.max_selections

        self._modifier_repo.save_group(group)
        return UpdateModifierGroupResponse(
            id=group.id,
            name=group.name,
            min_selections=group.min_selections,
            max_selections=group.max_selections,
        )
