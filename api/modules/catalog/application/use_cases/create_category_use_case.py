from modules.catalog.application.ports.driver.create_category_ports import (
    CreateCategoryCommand,
    CreateCategoryPort,
    CreateCategoryResponse,
)
from modules.catalog.application.ports.driven.category_repository_port import (
    CategoryRepositoryPort,
)
from modules.catalog.application.ports.driven.id_generator_port import IdGeneratorPort
from modules.catalog.domain.models.category import Category


class CreateCategoryUseCase(CreateCategoryPort):
    def __init__(
            self,
            categories: CategoryRepositoryPort,
            id_generator: IdGeneratorPort,
    ) -> None:
        self._categories = categories
        self._id_generator = id_generator

    def execute(self, command: CreateCategoryCommand) -> CreateCategoryResponse:
        category = Category(
            id=self._id_generator.generate(),
            description=command.description,
        )
        self._categories.save(category)

        return CreateCategoryResponse(
            id=category.id,
            description=category.description,
        )
    