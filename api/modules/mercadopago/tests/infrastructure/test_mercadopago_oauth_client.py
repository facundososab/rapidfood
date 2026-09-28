import re
from urllib.parse import parse_qs, urlparse

import pytest

from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoConfigurationError,
    MercadoPagoOAuthError,
)
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_oauth_client import (
    DEFAULT_API_BASE_URL,
    DEFAULT_AUTH_BASE_URL,
    MercadoPagoOAuthClient,
    MercadoPagoOAuthSettings,
    generate_pkce_challenge,
    generate_pkce_verifier,
)

AUTHORIZATION_REDIRECT_URI = "https://panel.example/api/mercadopago/callback/"


class FakeHttpError(Exception):
    pass


class FakeResponse:
    def __init__(self, payload, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise FakeHttpError(f"{self.status_code} error")

    def json(self):
        return self._payload


class FakeHttp:
    """Stand-in for the ``requests`` module: records the exact call."""

    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def post(self, url, data=None, headers=None, timeout=None):
        self.calls.append(
            {"url": url, "data": data, "headers": headers, "timeout": timeout}
        )
        if self.error is not None:
            raise self.error
        return self.response


def make_settings(**overrides) -> MercadoPagoOAuthSettings:
    values = {
        "client_id": "1234",
        "client_secret": "s3cr3t",
        "redirect_uri": AUTHORIZATION_REDIRECT_URI,
    }
    values.update(overrides)
    return MercadoPagoOAuthSettings(**values)


def query_of(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def test_builds_authorization_url_with_the_expected_query_parameters():
    client = MercadoPagoOAuthClient(make_settings(), http=FakeHttp())

    url = client.build_authorization_url("signed-state")

    parsed = urlparse(url)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == (
        f"{DEFAULT_AUTH_BASE_URL}/authorization"
    )
    assert query_of(url) == {
        "client_id": ["1234"],
        "response_type": ["code"],
        "platform_id": ["mp"],
        "redirect_uri": [AUTHORIZATION_REDIRECT_URI],
        "state": ["signed-state"],
    }


@pytest.mark.parametrize(
    ("missing_field", "expected_env"),
    [
        ("client_id", "MERCADOPAGO_CLIENT_ID"),
        ("redirect_uri", "MERCADOPAGO_REDIRECT_URI"),
    ],
)
def test_authorization_url_requires_the_oauth_application_settings(
    missing_field, expected_env
):
    settings = make_settings(**{missing_field: None})
    client = MercadoPagoOAuthClient(settings, http=FakeHttp())

    with pytest.raises(MercadoPagoConfigurationError, match=expected_env):
        client.build_authorization_url("signed-state", code_challenge="challenge-value")


def test_authorization_url_succeeds_without_a_client_secret():
    client = MercadoPagoOAuthClient(
        make_settings(client_secret=""),
        http=FakeHttp(),
    )

    url = client.build_authorization_url("signed-state")

    assert query_of(url)["client_id"] == ["1234"]


def test_authorization_url_carries_the_pkce_challenge_when_given():
    client = MercadoPagoOAuthClient(
        make_settings(client_secret=None),
        http=FakeHttp(),
    )

    url = client.build_authorization_url("signed-state", code_challenge="challenge-value")

    query = query_of(url)
    assert query["code_challenge"] == ["challenge-value"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == ["signed-state"]


def test_generate_pkce_verifier_matches_the_rfc7636_shape():
    verifier = generate_pkce_verifier()

    assert len(verifier) == 43
    assert re.fullmatch(r"[A-Za-z0-9\-._~]+", verifier)
    assert generate_pkce_verifier() != verifier


def test_generate_pkce_challenge_is_the_s256_hash_of_the_verifier():
    # RFC 7636 appendix B test vector.
    challenge = generate_pkce_challenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")

    assert challenge == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


def test_generate_pkce_pair_returns_a_challenge_matching_the_verifier():
    client = MercadoPagoOAuthClient(make_settings(client_secret=None), http=FakeHttp())

    verifier, challenge = client.generate_pkce_pair()

    assert generate_pkce_challenge(verifier) == challenge


def test_settings_default_to_the_production_mercadopago_hosts(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_CLIENT_ID", "app-id")
    monkeypatch.setenv("MERCADOPAGO_CLIENT_SECRET", "app-secret")
    monkeypatch.setenv("MERCADOPAGO_REDIRECT_URI", AUTHORIZATION_REDIRECT_URI)
    monkeypatch.delenv("MERCADOPAGO_AUTH_BASE_URL", raising=False)
    monkeypatch.delenv("MERCADOPAGO_API_BASE_URL", raising=False)

    settings = MercadoPagoOAuthSettings.from_env()

    assert settings.client_id == "app-id"
    assert settings.auth_base_url == DEFAULT_AUTH_BASE_URL
    assert settings.api_base_url == DEFAULT_API_BASE_URL


def test_settings_honor_environment_overrides(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_AUTH_BASE_URL", "https://sandbox.auth.example")
    monkeypatch.setenv("MERCADOPAGO_API_BASE_URL", "https://sandbox.api.example")

    settings = MercadoPagoOAuthSettings.from_env()

    assert settings.auth_base_url == "https://sandbox.auth.example"
    assert settings.api_base_url == "https://sandbox.api.example"


def test_exchange_code_posts_the_authorization_code_grant():
    http = FakeHttp(
        response=FakeResponse(
            {
                "access_token": "APP_USR-access",
                "refresh_token": "TG-refresh",
                "user_id": 987654321,
                "public_key": "APP_USR-public-key",
                "live_mode": True,
            }
        )
    )
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    result = client.exchange_code("auth-code")

    assert result.access_token == "APP_USR-access"
    assert result.refresh_token == "TG-refresh"
    assert result.user_id == "987654321"
    assert result.public_key == "APP_USR-public-key"
    assert result.live_mode is True

    assert len(http.calls) == 1
    call = http.calls[0]
    assert call["url"] == f"{DEFAULT_API_BASE_URL}/oauth/token"
    assert call["data"] == {
        "grant_type": "authorization_code",
        "client_id": "1234",
        "client_secret": "s3cr3t",
        "code": "auth-code",
        "redirect_uri": AUTHORIZATION_REDIRECT_URI,
    }


def test_exchange_code_without_a_client_secret_uses_the_pkce_verifier():
    http = FakeHttp(response=FakeResponse({"access_token": "APP_USR-access"}))
    client = MercadoPagoOAuthClient(make_settings(client_secret=None), http=http)

    result = client.exchange_code("auth-code", code_verifier="pkce-verifier")

    assert result.access_token == "APP_USR-access"
    assert http.calls[0]["data"] == {
        "grant_type": "authorization_code",
        "client_id": "1234",
        "code": "auth-code",
        "redirect_uri": AUTHORIZATION_REDIRECT_URI,
        "code_verifier": "pkce-verifier",
    }
    assert "client_secret" not in http.calls[0]["data"]


def test_exchange_code_omits_the_code_verifier_when_not_given():
    http = FakeHttp(response=FakeResponse({"access_token": "APP_USR-access"}))
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    client.exchange_code("auth-code")

    assert http.calls[0]["data"]["client_secret"] == "s3cr3t"
    assert "code_verifier" not in http.calls[0]["data"]


def test_exchange_code_without_a_client_secret_still_rejects_a_tokenless_response():
    http = FakeHttp(response=FakeResponse({"error": "invalid_grant"}, status_code=200))
    client = MercadoPagoOAuthClient(make_settings(client_secret=""), http=http)

    with pytest.raises(MercadoPagoOAuthError, match="invalid_grant"):
        client.exchange_code("auth-code", code_verifier="pkce-verifier")


@pytest.mark.parametrize(
    ("raw_live_mode", "expected"),
    [(True, True), ("true", True), ("True", True), ("1", True), (1, True),
     (False, False), ("false", False), ("0", False), (0, False), (None, False)],
)
def test_exchange_code_adapts_the_live_mode_flag(raw_live_mode, expected):
    http = FakeHttp(
        response=FakeResponse(
            {"access_token": "APP_USR-access", "live_mode": raw_live_mode}
        )
    )
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    result = client.exchange_code("auth-code")

    assert result.live_mode is expected


def test_exchange_code_accepts_a_response_without_optional_fields():
    http = FakeHttp(response=FakeResponse({"access_token": "APP_USR-access"}))
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    result = client.exchange_code("auth-code")

    assert result.access_token == "APP_USR-access"
    assert result.refresh_token is None
    assert result.user_id is None
    assert result.public_key is None
    assert result.live_mode is False


def test_exchange_code_prefers_the_explicit_redirect_uri():
    http = FakeHttp(response=FakeResponse({"access_token": "APP_USR-access"}))
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    client.exchange_code("auth-code", "https://override.example/callback/")

    assert http.calls[0]["data"]["redirect_uri"] == "https://override.example/callback/"


def test_exchange_code_uses_the_configured_api_base_url():
    http = FakeHttp(response=FakeResponse({"access_token": "APP_USR-access"}))
    client = MercadoPagoOAuthClient(
        make_settings(api_base_url="https://sandbox.api.example"),
        http=http,
    )

    client.exchange_code("auth-code")

    assert http.calls[0]["url"] == "https://sandbox.api.example/oauth/token"


def test_exchange_code_requires_the_client_id():
    client = MercadoPagoOAuthClient(make_settings(client_id=None), http=FakeHttp())

    with pytest.raises(MercadoPagoConfigurationError, match="MERCADOPAGO_CLIENT_ID"):
        client.exchange_code("auth-code", code_verifier="pkce-verifier")


def test_exchange_code_translates_http_failures():
    http = FakeHttp(response=FakeResponse({"error": "invalid_grant"}, status_code=400))
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    with pytest.raises(MercadoPagoOAuthError):
        client.exchange_code("auth-code")


def test_exchange_code_translates_transport_failures():
    http = FakeHttp(error=RuntimeError("connection refused"))
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    with pytest.raises(MercadoPagoOAuthError, match="token exchange failed"):
        client.exchange_code("auth-code")


def test_exchange_code_reports_the_mercadopago_rejection_code():
    http = FakeHttp(
        response=FakeResponse({"error": "invalid_grant"}, status_code=200)
    )
    client = MercadoPagoOAuthClient(make_settings(), http=http)

    with pytest.raises(MercadoPagoOAuthError, match="invalid_grant"):
        client.exchange_code("auth-code")
