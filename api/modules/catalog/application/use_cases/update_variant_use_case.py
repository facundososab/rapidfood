from modules.catalog.application.ports.driver.update_variant_ports import (
    UpdateVariantPort, UpdateVariantCommand, UpdateVariantResponse,
)
from modules.catalog.application.ports.driven.variant_repository_port import VariantRepositoryPort
from modules.catalog.domain.errors.catalog_errors import VariantNotFoundError


class UpdateVariantUseCase(UpdateVariantPort):
    def __init__(self, variant_repo: VariantRepositoryPort) -> None:
        self._variant_repo = variant_repo

    def execute(self, command: UpdateVariantCommand) -> UpdateVariantResponse:
        variant = self._variant_repo.find_by_id(command.variant_id)
        if variant is None:
            raise VariantNotFoundError(command.variant_id)

        if command.name is not None:
            variant.name = command.name
        if command.available is not None:
            variant.available = command.available

        self._variant_repo.save(variant)

        return UpdateVariantResponse(
            id=variant.id,
            name=variant.name,
            available=variant.available,
        )
