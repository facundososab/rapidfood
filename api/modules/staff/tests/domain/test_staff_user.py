import pytest

from modules.staff.domain.models.staff_user import StaffRole, StaffUser


def test_create_staff_user_valid() -> None:
    staff = StaffUser.create(
        staff_id="00000000-0000-0000-0000-000000000001",
        supabase_auth_id="auth-user-1",
        email="caja@rapidfood.local",
        name="Caja Uno",
        role=StaffRole.CASHIER,
    )

    assert staff.id == "00000000-0000-0000-0000-000000000001"
    assert staff.supabase_auth_id == "auth-user-1"
    assert staff.role == StaffRole.CASHIER
    assert staff.business_config_id is None


def test_blank_name_rejected() -> None:
    with pytest.raises(ValueError):
        StaffUser.create(
            staff_id="id", supabase_auth_id="auth", email="a@b.c", name="  ", role=StaffRole.ADMIN
        )


def test_blank_email_rejected() -> None:
    with pytest.raises(ValueError):
        StaffUser.create(
            staff_id="id", supabase_auth_id="auth", email="  ", name="X", role=StaffRole.ADMIN
        )


def test_invalid_role_rejected() -> None:
    with pytest.raises(ValueError):
        StaffUser(id="id", supabase_auth_id="auth", email="a@b.c", name="X", role="OWNER")


def test_enum_members_match_database() -> None:
    assert [r.value for r in StaffRole] == ["ADMIN", "CASHIER", "KITCHEN"]