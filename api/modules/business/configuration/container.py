"""Composition root for the business module."""

from __future__ import annotations

from modules.business.application.use_cases.create_address_use_case import CreateAddressUseCase
from modules.business.application.use_cases.update_address_use_case import UpdateAddressUseCase
from modules.business.application.use_cases.delete_address_use_case import DeleteAddressUseCase
from modules.business.application.use_cases.get_business_configuration_use_case import GetBusinessConfigurationUseCase
from modules.business.application.use_cases.save_business_configuration_use_case import SaveBusinessConfigurationUseCase
from modules.business.application.use_cases.upsert_business_hours_use_case import UpsertBusinessHoursUseCase
from modules.business.infrastructure.adapters.driven.prisma.business_configuration_repository import (
    PrismaBusinessConfigurationRepository,
)


class BusinessContainer:
    def __init__(self) -> None:
        repo = PrismaBusinessConfigurationRepository()
        self.get_configuration = GetBusinessConfigurationUseCase(repo)
        self.save_configuration = SaveBusinessConfigurationUseCase(repo)
        self.upsert_hours = UpsertBusinessHoursUseCase(repo)
        self.create_address = CreateAddressUseCase(repo)
        self.update_address = UpdateAddressUseCase(repo)
        self.delete_address = DeleteAddressUseCase(repo)


def get_business_container() -> BusinessContainer:
    return BusinessContainer()
