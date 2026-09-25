from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.mercadopago.application.ports.driver.build_authorization_url_port import (
    BuildAuthorizationUrlResult,
)
from modules.mercadopago.application.ports.driver.get_link_status_port import (
    GetLinkStatusResult,
)
from modules.mercadopago.application.ports.driver.link_mercadopago_account_port import (
    LinkMercadoPagoAccountResult,
)
from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoConfigurationError,
    MercadoPagoOAuthError,
    MercadoPagoStateError,
)
from modules.mercadopago.infrastructure.adapters.driver.rest import views
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_oauth_client import (
    MercadoPagoOAuthSettings,
)
from modules.mercadopago.tests.use_cases.fakes import BUSINESS_CONFIG_ID
from shared.infrastructure.auth.supabase_jwt import SupabasePrincipal

AUTHORIZATION_URL = "https://auth.mercadopago.com/authorization?state=signed-state"
PANEL_RETURN_URI = "https://panel.example/configuracion/pagos/"


class FakeUseCase:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.commands: list = []

    def execute(self, command):
        self.commands.append(command)
        if self.error is not None:
            raise self.error
        return self.result


class FakeContainer:
    def __init__(
        self,
        authorize_error: Exception | None = None,
        link_error: Exception | None = None,
        link_result: LinkMercadoPagoAccountResult | None = None,
        status_result: GetLinkStatusResult | None = None,
        return_uri: str | None = None,
    ) -> None:
        # The real settings type keeps the driver contract honest (the view only
        # reads return_uri); None preserves the JSON callback behaviour.
        self.settings = MercadoPagoOAuthSettings(return_uri=return_uri)
        self.build_authorization_url = FakeUseCase(
            result=BuildAuthorizationUrlResult(authorization_url=AUTHORIZATION_URL),
            error=authorize_error,
        )
        self.link_account = FakeUseCase(
            result=link_result
            if link_result is not None
            else LinkMercadoPagoAccountResult(
                credential_id="33333333-3333-3333-3333-333333333333",
                business_config_id=BUSINESS_CONFIG_ID,
                live_mode=True,
                user_id="987654321",
            ),
            error=link_error,
        )
        self.get_link_status = FakeUseCase(
            result=status_result
            if status_result is not None
            else GetLinkStatusResult(
                linked=True,
                live_mode=True,
                user_id="987654321",
                public_key="APP_USR-public-key",
            )
        )
        self.unlink_account = FakeUseCase(result=None)


def patch_container(monkeypatch, container: FakeContainer) -> None:
    monkeypatch.setattr(views, "get_app_mercadopago_container", lambda: container)


def authenticated(request):
    force_authenticate(request, user=SupabasePrincipal(id="auth-user-1"))
    return request


def test_authorize_returns_the_authorization_url(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().post(
        "/api/mercadopago/authorize/",
        {"business_config_id": BUSINESS_CONFIG_ID},
        format="json",
    )

    response = views.MercadoPagoAuthorizeView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"authorization_url": AUTHORIZATION_URL}
    assert container.build_authorization_url.commands[0].business_config_id == (
        BUSINESS_CONFIG_ID
    )


def test_authorize_requires_authentication():
    request = APIRequestFactory().post(
        "/api/mercadopago/authorize/",
        {"business_config_id": BUSINESS_CONFIG_ID},
        format="json",
    )

    response = views.MercadoPagoAuthorizeView.as_view()(request)

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


def test_authorize_rejects_a_missing_business_config_id(monkeypatch):
    patch_container(monkeypatch, FakeContainer())
    request = APIRequestFactory().post("/api/mercadopago/authorize/", {}, format="json")

    response = views.MercadoPagoAuthorizeView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_authorize_rejects_an_invalid_uuid(monkeypatch):
    patch_container(monkeypatch, FakeContainer())
    request = APIRequestFactory().post(
        "/api/mercadopago/authorize/",
        {"business_config_id": "not-a-uuid"},
        format="json",
    )

    response = views.MercadoPagoAuthorizeView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_authorize_reports_missing_oauth_configuration(monkeypatch):
    patch_container(
        monkeypatch,
        FakeContainer(
            authorize_error=MercadoPagoConfigurationError(
                "Mercado Pago is not configured: MERCADOPAGO_CLIENT_ID is missing"
            )
        ),
    )
    request = APIRequestFactory().post(
        "/api/mercadopago/authorize/",
        {"business_config_id": BUSINESS_CONFIG_ID},
        format="json",
    )

    response = views.MercadoPagoAuthorizeView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "MERCADOPAGO_CLIENT_ID" in response.data["error"]


def test_callback_links_the_account_without_authentication(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().get(
        "/api/mercadopago/callback/",
        {"code": "auth-code", "state": "signed-state"},
    )

    response = views.MercadoPagoCallbackView.as_view()(request)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "linked": True,
        "business_config_id": BUSINESS_CONFIG_ID,
        "live_mode": True,
    }
    command = container.link_account.commands[0]
    assert command.code == "auth-code"
    assert command.state == "signed-state"
    assert command.redirect_uri is None


def test_callback_forwards_an_optional_redirect_uri_override(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().get(
        "/api/mercadopago/callback/",
        {
            "code": "auth-code",
            "state": "signed-state",
            "redirect_uri": "https://override.example/callback/",
        },
    )

    views.MercadoPagoCallbackView.as_view()(request)

    assert container.link_account.commands[0].redirect_uri == (
        "https://override.example/callback/"
    )


def test_callback_requires_code_and_state(monkeypatch):
    patch_container(monkeypatch, FakeContainer())
    request = APIRequestFactory().get("/api/mercadopago/callback/", {"code": "c"})

    response = views.MercadoPagoCallbackView.as_view()(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_callback_returns_400_for_an_invalid_state(monkeypatch):
    patch_container(
        monkeypatch,
        FakeContainer(link_error=MercadoPagoStateError("Mercado Pago OAuth state is invalid")),
    )
    request = APIRequestFactory().get(
        "/api/mercadopago/callback/",
        {"code": "auth-code", "state": "tampered"},
    )

    response = views.MercadoPagoCallbackView.as_view()(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Mercado Pago OAuth state is invalid"


def test_callback_returns_502_when_mercadopago_rejects_the_code(monkeypatch):
    patch_container(
        monkeypatch,
        FakeContainer(
            link_error=MercadoPagoOAuthError("Mercado Pago rejected the token exchange")
        ),
    )
    request = APIRequestFactory().get(
        "/api/mercadopago/callback/",
        {"code": "auth-code", "state": "signed-state"},
    )

    response = views.MercadoPagoCallbackView.as_view()(request)

    assert response.status_code == status.HTTP_502_BAD_GATEWAY


def test_callback_redirects_to_the_panel_after_linking(monkeypatch):
    container = FakeContainer(return_uri=PANEL_RETURN_URI)
    patch_container(monkeypatch, container)
    request = APIRequestFactory().get(
        "/api/mercadopago/callback/",
        {"code": "auth-code", "state": "signed-state"},
    )

    response = views.MercadoPagoCallbackView.as_view()(request)

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"].endswith("?mp=linked")
    assert response["Location"] == f"{PANEL_RETURN_URI.rstrip('/')}?mp=linked"
    # The panel is the only thing the browser sees: the link itself still ran.
    assert len(container.link_account.commands) == 1


def test_callback_redirects_to_the_panel_when_the_state_is_invalid(monkeypatch):
    patch_container(
        monkeypatch,
        FakeContainer(
            return_uri=PANEL_RETURN_URI,
            link_error=MercadoPagoStateError("Mercado Pago OAuth state is invalid"),
        ),
    )
    request = APIRequestFactory().get(
        "/api/mercadopago/callback/",
        {"code": "auth-code", "state": "tampered"},
    )

    response = views.MercadoPagoCallbackView.as_view()(request)

    assert response.status_code == status.HTTP_302_FOUND
    assert response["Location"].endswith("?mp=error")
    assert response["Location"] == f"{PANEL_RETURN_URI.rstrip('/')}?mp=error"


def test_status_returns_the_linked_account(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().get(
        "/api/mercadopago/status/",
        {"business_config_id": BUSINESS_CONFIG_ID},
    )

    response = views.MercadoPagoStatusView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "linked": True,
        "live_mode": True,
        "user_id": "987654321",
        "public_key": "APP_USR-public-key",
    }
    assert container.get_link_status.commands[0].business_config_id == BUSINESS_CONFIG_ID


def test_status_reports_an_unlinked_business(monkeypatch):
    patch_container(monkeypatch, FakeContainer(status_result=GetLinkStatusResult(linked=False)))
    request = APIRequestFactory().get(
        "/api/mercadopago/status/",
        {"business_config_id": BUSINESS_CONFIG_ID},
    )

    response = views.MercadoPagoStatusView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "linked": False,
        "live_mode": None,
        "user_id": None,
        "public_key": None,
    }


def test_status_requires_authentication(monkeypatch):
    patch_container(monkeypatch, FakeContainer())
    request = APIRequestFactory().get(
        "/api/mercadopago/status/",
        {"business_config_id": BUSINESS_CONFIG_ID},
    )

    response = views.MercadoPagoStatusView.as_view()(request)

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


def test_status_rejects_an_invalid_uuid(monkeypatch):
    patch_container(monkeypatch, FakeContainer())
    request = APIRequestFactory().get(
        "/api/mercadopago/status/",
        {"business_config_id": "nope"},
    )

    response = views.MercadoPagoStatusView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_unlink_returns_204(monkeypatch):
    container = FakeContainer()
    patch_container(monkeypatch, container)
    request = APIRequestFactory().post(
        "/api/mercadopago/unlink/",
        {"business_config_id": BUSINESS_CONFIG_ID},
        format="json",
    )

    response = views.MercadoPagoUnlinkView.as_view()(authenticated(request))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert container.unlink_account.commands[0].business_config_id == BUSINESS_CONFIG_ID


def test_unlink_requires_authentication(monkeypatch):
    patch_container(monkeypatch, FakeContainer())
    request = APIRequestFactory().post(
        "/api/mercadopago/unlink/",
        {"business_config_id": BUSINESS_CONFIG_ID},
        format="json",
    )

    response = views.MercadoPagoUnlinkView.as_view()(request)

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )
