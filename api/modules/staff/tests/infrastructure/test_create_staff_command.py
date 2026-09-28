"""Unit tests for the create_staff management command (no DB, no network).

Note: call_command() instantiates its own Command, so fakes must patch the
CLASS methods, not a manual instance.
"""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from modules.staff.domain.models.staff_user import StaffRole
from modules.staff.management.commands.create_staff import Command


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abcdefgh.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "svc-role-key")
    yield


def _fake_supabase_user(monkeypatch, **overrides):
    def fake(self, settings, email: str, password: str) -> dict:
        payload = {"id": "auth-user-123", "email": email}
        payload.update(overrides)
        return payload

    monkeypatch.setattr(Command, "_create_supabase_user", fake)


def test_happy_path_creates_user_and_staff_row(monkeypatch) -> None:
    created = {}

    def fake_staff_row(self, supabase_auth_id, email, name, role):
        created["supabase_auth_id"] = supabase_auth_id
        created["email"] = email
        created["name"] = name
        created["role"] = role

    _fake_supabase_user(monkeypatch)
    monkeypatch.setattr(Command, "_create_staff_row", fake_staff_row)

    call_command(
        "create_staff",
        email="caja@rapidfood.local",
        name="Caja Uno",
        role="CASHIER",
        password="initial-pass",
    )

    assert created == {
        "supabase_auth_id": "auth-user-123",
        "email": "caja@rapidfood.local",
        "name": "Caja Uno",
        "role": StaffRole.CASHIER,
    }


def test_rejects_unconfigured_service_role_key(monkeypatch) -> None:
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY")

    with pytest.raises(CommandError, match="SUPABASE_SERVICE_ROLE_KEY is not set"):
        call_command("create_staff", email="a@b.c", name="X", role="ADMIN")


def test_rejects_role_outside_enum() -> None:
    with pytest.raises(CommandError, match="invalid choice"):
        call_command("create_staff", email="a@b.c", name="X", role="OWNER")


def test_propagates_supabase_admin_failure(monkeypatch) -> None:
    def boom(self, settings, email: str, password: str) -> dict:
        raise CommandError("Supabase admin API rejected user creation (HTTP 400): nope")

    monkeypatch.setattr(Command, "_create_supabase_user", boom)

    with pytest.raises(CommandError, match="HTTP 400"):
        call_command("create_staff", email="a@b.c", name="X", role="ADMIN")


def test_propagates_staff_row_failure(monkeypatch) -> None:
    _fake_supabase_user(monkeypatch)

    def boom(self, supabase_auth_id, email, name, role):
        raise CommandError("Supabase user was created but the staff row failed: dup")

    monkeypatch.setattr(Command, "_create_staff_row", boom)

    with pytest.raises(CommandError, match="staff row failed"):
        call_command("create_staff", email="a@b.c", name="X", role="ADMIN")