import pytest

from modules.mercadopago.application.ports.driver.build_authorization_url_port import (
    BuildAuthorizationUrlCommand,
)
from modules.mercadopago.application.use_cases.build_authorization_url_use_case import (
    BuildAuthorizationUrlUseCase,
)
from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoConfigurationError,
)
from modules.mercadopago.tests.use_cases.fakes import (
    AUTHORIZATION_BASE_URL,
    BUSINESS_CONFIG_ID,
    FakeMercadoPagoOAuthClient,
    FakeStateSigner,
)


def test_builds_authorization_url_from_the_signed_state():
    oauth_client = FakeMercadoPagoOAuthClient()
    state_signer = FakeStateSigner()
    use_case = BuildAuthorizationUrlUseCase(oauth_client, state_signer)

    result = use_case.execute(
        BuildAuthorizationUrlCommand(business_config_id=BUSINESS_CONFIG_ID)
    )

    assert state_signer.signed_business_ids == [BUSINESS_CONFIG_ID]
    assert len(oauth_client.received_states) == 1
    assert result.authorization_url == (
        f"{AUTHORIZATION_BASE_URL}?state={oauth_client.received_states[0]}"
    )


def test_propagates_missing_oauth_configuration():
    oauth_client = FakeMercadoPagoOAuthClient(
        authorize_error=MercadoPagoConfigurationError(
            "Mercado Pago is not configured: MERCADOPAGO_CLIENT_ID is missing"
        )
    )
    use_case = BuildAuthorizationUrlUseCase(oauth_client, FakeStateSigner())

    with pytest.raises(MercadoPagoConfigurationError, match="MERCADOPAGO_CLIENT_ID"):
        use_case.execute(
            BuildAuthorizationUrlCommand(business_config_id=BUSINESS_CONFIG_ID)
        )
