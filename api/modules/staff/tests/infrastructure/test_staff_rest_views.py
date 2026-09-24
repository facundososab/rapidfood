from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.staff.domain.errors.staff_errors import StaffNotFoundError
from modules.staff.domain.models.staff_user import StaffRole
from modules.staff.infrastructure.adapters.driver.rest import views as staff_views
from modules.staff.tests.use_cases.fakes import STAFF_ID, make_staff
from shared.infrastructure.auth.supabase_jwt import SupabasePrincipal


def _principal(sub: str = "auth-user-1") -> SupabasePrincipal:
    return SupabasePrincipal(id=sub, email="caja@rapidfood.local")


def _as_authenticated(request, principal=_principal()) -> None:
    force_authenticate(request, user=principal)


class _FakeUseCase:
    def __init__(self, result=None, error: bool = False) -> None:
        self._result = result
        self._error = error

    def execute(self, query):
        if self._error:
            raise StaffNotFoundError(query.supabase_auth_id)
        return self._result


class _FakeContainer:
    def __init__(self, result=None, error: bool = False) -> None:
        self.get_current_staff = _FakeUseCase(result=result, error=error)


def _call_me(request):
    return staff_views.MeView.as_view()(request)


def test_me_returns_staff_profile_when_authenticated(monkeypatch) -> None:
    staff = make_staff(role=StaffRole.KITCHEN)
    monkeypatch.setattr(staff_views, "get_app_staff_container", lambda: _FakeContainer(result=staff))

    factory = APIRequestFactory()
    request = factory.get("/api/staff/me/")
    _as_authenticated(request)

    response = _call_me(request)

    assert response.status_code == status.HTTP_200_OK
    body = response.data
    assert body["id"] == STAFF_ID
    assert body["email"] == "caja@rapidfood.local"
    assert body["role"] == "KITCHEN"
    assert body["businessConfigId"] is None


def test_me_requires_authentication() -> None:
    factory = APIRequestFactory()
    request = factory.get("/api/staff/me/")

    response = _call_me(request)

    # 403 (PermissionDenied), not 401, until the global DRF auth class is
    # enabled (work unit 5 — then DRF raises NotAuthenticated/401).
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_me_404_when_identity_is_not_staff(monkeypatch) -> None:
    monkeypatch.setattr(staff_views, "get_app_staff_container", lambda: _FakeContainer(error=True))

    factory = APIRequestFactory()
    request = factory.get("/api/staff/me/")
    _as_authenticated(request)

    response = _call_me(request)

    assert response.status_code == status.HTTP_404_NOT_FOUND