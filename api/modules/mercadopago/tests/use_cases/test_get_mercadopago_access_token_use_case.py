from modules.mercadopago.application.ports.driver.get_mercadopago_access_token_port import (
    GetMercadoPagoAccessTokenQuery,
)
from modules.mercadopago.application.use_cases.get_mercadopago_access_token_use_case import (
    GetMercadoPagoAccessTokenUseCase,
)
from modules.mercadopago.tests.use_cases.fakes import (
    BUSINESS_CONFIG_ID,
    OTHER_BUSINESS_CONFIG_ID,
    FakeMercadoPagoCredentialRepository,
    make_credential,
)


def test_returns_the_linked_access_token_of_the_business():
    repository = FakeMercadoPagoCredentialRepository(
        {BUSINESS_CONFIG_ID: make_credential(access_token="APP_USR-linked-token")}
    )
    use_case = GetMercadoPagoAccessTokenUseCase(repository)

    token = use_case.execute(
        GetMercadoPagoAccessTokenQuery(business_config_id=BUSINESS_CONFIG_ID)
    )

    assert token == "APP_USR-linked-token"


def test_returns_none_when_the_business_is_not_linked():
    use_case = GetMercadoPagoAccessTokenUseCase(FakeMercadoPagoCredentialRepository())

    token = use_case.execute(
        GetMercadoPagoAccessTokenQuery(business_config_id=BUSINESS_CONFIG_ID)
    )

    assert token is None


def test_another_business_token_is_not_returned():
    repository = FakeMercadoPagoCredentialRepository(
        {BUSINESS_CONFIG_ID: make_credential(access_token="APP_USR-linked-token")}
    )
    use_case = GetMercadoPagoAccessTokenUseCase(repository)

    token = use_case.execute(
        GetMercadoPagoAccessTokenQuery(business_config_id=OTHER_BUSINESS_CONFIG_ID)
    )

    assert token is None
