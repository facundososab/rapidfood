from modules.staff.domain.models.staff_user import StaffRole, StaffUser

STAFF_ID = "00000000-0000-0000-0000-000000000001"
AUTH_ID = "auth-user-1"


class FakeStaffRepository:
    """In-memory StaffRepositoryPort for use-case tests."""

    def __init__(self, staff: StaffUser | None = None) -> None:
        self.staff = staff

    def get_by_supabase_auth_id(self, supabase_auth_id: str) -> StaffUser | None:
        if self.staff is not None and self.staff.supabase_auth_id == supabase_auth_id:
            return self.staff
        return None

    def get_by_email(self, email: str) -> StaffUser | None:
        if self.staff is not None and self.staff.email == email:
            return self.staff
        return None


def make_staff(**overrides) -> StaffUser:
    values = {
        "staff_id": STAFF_ID,
        "supabase_auth_id": AUTH_ID,
        "email": "caja@rapidfood.local",
        "name": "Caja Uno",
        "role": StaffRole.CASHIER,
    }
    values.update(overrides)
    return StaffUser.create(**values)