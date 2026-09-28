from functools import lru_cache

from modules.staff.application.use_cases.get_current_staff_use_case import (
    GetCurrentStaffUseCase,
)
from modules.staff.infrastructure.adapters.driven.prisma.staff_repository import (
    PrismaStaffRepository,
)


class StaffContainer:
    def __init__(self) -> None:
        staff_repository = PrismaStaffRepository()
        self.get_current_staff = GetCurrentStaffUseCase(staff_repository)


@lru_cache(maxsize=1)
def get_staff_container() -> StaffContainer:
    return StaffContainer()