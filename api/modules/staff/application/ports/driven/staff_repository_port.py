from typing import Protocol

from modules.staff.domain.models.staff_user import StaffUser


class StaffRepositoryPort(Protocol):
    """Driven port: persistence of staff members."""

    def get_by_supabase_auth_id(self, supabase_auth_id: str) -> StaffUser | None: ...

    def get_by_email(self, email: str) -> StaffUser | None: ...