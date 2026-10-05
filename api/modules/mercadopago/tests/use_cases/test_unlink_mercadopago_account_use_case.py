from modules.mercadopago.application.ports.driver.unlink_mercadopago_account_port import (
    UnlinkMercadoPagoAccountCommand,
)
from modules.mercadopago.application.use_cases.unlink_mercadopago_account_use_case import (
    UnlinkMercadoPagoAccountUseCase,
)
from modules.mercadopago.tests.use_cases.fakes import (
    BUSINESS_CONFIG_ID,
    FakeMercadoPagoCredentialRepository,
    make_credential,
)


def test_removes_the_existing_link():
    repository = FakeMercadoPagoCredentialRepository(
        {BUSINESS_CONFIG_ID: make_credential()}
    )
    use_case = UnlinkMercadoPagoAccountUseCase(repository)

    result = use_case.execute(
        UnlinkMercadoPagoAccountCommand(business_config_id=BUSINESS_CONFIG_ID)
    )

    assert result is None
    assert repository.deleted == [BUSINESS_CONFIG_ID]
    assert repository.get_by_business(BUSINESS_CONFIG_ID) is None


def test_is_idempotent_when_the_business_was_never_linked():
    repository = FakeMercadoPagoCredentialRepository()
    use_case = UnlinkMercadoPagoAccountUseCase(repository)

    use_case.execute(
        UnlinkMercadoPagoAccountCommand(business_config_id=BUSINESS_CONFIG_ID)
    )
    use_case.execute(
        UnlinkMercadoPagoAccountCommand(business_config_id=BUSINESS_CONFIG_ID)
    )

    assert repository.deleted == [BUSINESS_CONFIG_ID, BUSINESS_CONFIG_ID]
