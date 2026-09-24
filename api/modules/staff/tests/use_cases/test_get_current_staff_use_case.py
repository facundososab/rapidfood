import pytest

from modules.staff.application.ports.driver.get_current_staff_ports import (
    GetStaffBySupabaseAuthIdQuery,
)
from modules.staff.application.use_cases.get_current_staff_use_case import (
    GetCurrentStaffUseCase,
)
from modules.staff.domain.errors.staff_errors import StaffNotFoundError
from modules.staff.domain.models.staff_user import StaffRole
from modules.staff.tests.use_cases.fakes import AUTH_ID, FakeStaffRepository, make_staff


def test_returns_staff_for_known_identity() -> None:
    staff = make_staff(role=StaffRole.ADMIN)
    use_case = GetCurrentStaffUseCase(FakeStaffRepository(staff))

    result = use_case.execute(GetStaffBySupabaseAuthIdQuery(supabase_auth_id=AUTH_ID))

    assert result == staff
    assert result.role == StaffRole.ADMIN


def test_raises_not_found_for_unknown_identity() -> None:
    use_case = GetCurrentStaffUseCase(FakeStaffRepository(None))

    with pytest.raises(StaffNotFoundError):
        use_case.execute(GetStaffBySupabaseAuthIdQuery(supabase_auth_id="unknown"))