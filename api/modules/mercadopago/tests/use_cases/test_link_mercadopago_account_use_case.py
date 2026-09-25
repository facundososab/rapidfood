import pytest

from modules.mercadopago.application.ports.driven.mercadopago_oauth_client import (
    OAuthTokenResult,
)
from modules.mercadopago.application.ports.driver.link_mercadopago_account_port import (
    LinkMercadoPagoAccountCommand,
)
from modules.mercadopago.application.use_cases.link_mercadopago_account_use_case import (
    LinkMercadoPagoAccountUseCase,
)
from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoOAuthError,
    MercadoPagoStateError,
)
from modules.mercadopago.tests.use_cases.fakes import (
    BUSINESS_CONFIG_ID,
    FakeMercadoPagoCredentialRepository,
    FakeMercadoPagoOAuthClient,
    FakeStateSigner,
    make_credential,
)


def _use_case(
    repository=None,
    oauth_client=None,
    state_signer=None,
) -> tuple[LinkMercadoPagoAccountUseCase, FakeMercadoPagoCredentialRepository, FakeMercadoPagoOAuthClient, FakeStateSigner]:
    repository = repository if repository is not None else FakeMercadoPagoCredentialRepository()
    oauth_client = oauth_client if oauth_client is not None else FakeMercadoPagoOAuthClient()
    state_signer = state_signer if state_signer is not None else FakeStateSigner()
    return (
        LinkMercadoPagoAccountUseCase(repository, oauth_client, state_signer),
        repository,
        oauth_client,
        state_signer,
    )


def test_links_the_account_and_persists_the_exchanged_tokens():
    oauth_client = FakeMercadoPagoOAuthClient(
        tokens=OAuthTokenResult(
            access_token="APP_USR-access",
            refresh_token="TG-refresh",
            user_id="987654321",
            public_key="APP_USR-public-key",
            live_mode=True,
        )
    )
    use_case, repository, _, state_signer = _use_case(oauth_client=oauth_client)
    state = state_signer.sign(BUSINESS_CONFIG_ID)

    result = use_case.execute(
        LinkMercadoPagoAccountCommand(code="auth-code", state=state)
    )

    assert oauth_client.exchanged == [("auth-code", None)]
    assert len(repository.upserted) == 1
    persisted = repository.get_by_business(BUSINESS_CONFIG_ID)
    assert persisted is not None
    assert persisted.access_token == "APP_USR-access"
    assert persisted.refresh_token == "TG-refresh"
    assert persisted.live_mode is True
    assert result.business_config_id == BUSINESS_CONFIG_ID
    assert result.credential_id == persisted.credential_id
    assert result.live_mode is True
    assert result.user_id == "987654321"


def test_forwards_an_explicit_redirect_uri_override():
    use_case, _, oauth_client, state_signer = _use_case()
    state = state_signer.sign(BUSINESS_CONFIG_ID)

    use_case.execute(
        LinkMercadoPagoAccountCommand(
            code="auth-code",
            state=state,
            redirect_uri="https://panel.example/api/mercadopago/callback/",
        )
    )

    assert oauth_client.exchanged == [
        ("auth-code", "https://panel.example/api/mercadopago/callback/")
    ]


def test_relinking_replaces_the_stored_credentials():
    repository = FakeMercadoPagoCredentialRepository()
    repository.upsert(make_credential(access_token="APP_USR-old"))
    oauth_client = FakeMercadoPagoOAuthClient(
        tokens=OAuthTokenResult(access_token="APP_USR-new", live_mode=False)
    )
    use_case, _, _, state_signer = _use_case(
        repository=repository,
        oauth_client=oauth_client,
    )
    state = state_signer.sign(BUSINESS_CONFIG_ID)

    use_case.execute(LinkMercadoPagoAccountCommand(code="auth-code", state=state))

    assert len(repository.upserted) == 2
    persisted = repository.get_by_business(BUSINESS_CONFIG_ID)
    assert persisted is not None
    assert persisted.access_token == "APP_USR-new"
    assert persisted.live_mode is False


def test_rejects_a_tampered_state_before_talking_to_mercadopago():
    use_case, repository, oauth_client, _ = _use_case()

    with pytest.raises(MercadoPagoStateError, match="invalid"):
        use_case.execute(
            LinkMercadoPagoAccountCommand(code="auth-code", state="tampered-state")
        )

    assert oauth_client.exchanged == []
    assert repository.upserted == []


def test_rejects_an_expired_state():
    state_signer = FakeStateSigner(max_age_seconds=600)
    use_case, repository, oauth_client, _ = _use_case(state_signer=state_signer)
    state = state_signer.sign(BUSINESS_CONFIG_ID)
    state_signer.advance(601)

    with pytest.raises(MercadoPagoStateError, match="expired"):
        use_case.execute(LinkMercadoPagoAccountCommand(code="auth-code", state=state))

    assert oauth_client.exchanged == []
    assert repository.upserted == []


def test_propagates_oauth_failures_without_persisting():
    oauth_client = FakeMercadoPagoOAuthClient(
        exchange_error=MercadoPagoOAuthError("Mercado Pago rejected the token exchange")
    )
    use_case, repository, _, state_signer = _use_case(oauth_client=oauth_client)
    state = state_signer.sign(BUSINESS_CONFIG_ID)

    with pytest.raises(MercadoPagoOAuthError, match="rejected the token exchange"):
        use_case.execute(LinkMercadoPagoAccountCommand(code="auth-code", state=state))

    assert repository.upserted == []
    assert repository.get_by_business(BUSINESS_CONFIG_ID) is None
