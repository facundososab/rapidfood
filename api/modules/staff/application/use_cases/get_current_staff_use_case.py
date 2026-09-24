from modules.staff.application.ports.driven.staff_repository_port import (
    StaffRepositoryPort,
)
from modules.staff.application.ports.driver.get_current_staff_ports import (
    GetStaffBySupabaseAuthIdQuery,
)
from modules.staff.domain.errors.staff_errors import StaffNotFoundError
from modules.staff.domain.models.staff_user import StaffUser


class GetCurrentStaffUseCase:
    def __init__(self, repository: StaffRepositoryPort) -> None:
        self._repository = repository

    def execute(self, query: GetStaffBySupabaseAuthIdQuery) -> StaffUser:
        staff = self._repository.get_by_supabase_auth_id(query.supabase_auth_id)
        if staff is None:
            raise StaffNotFoundError(query.supabase_auth_id)
        return staff