import dataclasses

from modules.mercadopago.application.ports.driver.get_link_status_port import (
    GetLinkStatusQuery,
    GetLinkStatusResult,
)
from modules.mercadopago.application.use_cases.get_link_status_use_case import (
    GetLinkStatusUseCase,
)
from modules.mercadopago.tests.use_cases.fakes import (
    BUSINESS_CONFIG_ID,
    OTHER_BUSINESS_CONFIG_ID,
    FakeMercadoPagoCredentialRepository,
    make_credential,
)


def test_reports_unlinked_when_there_is_no_credential():
    use_case = GetLinkStatusUseCase(FakeMercadoPagoCredentialRepository())

    result = use_case.execute(GetLinkStatusQuery(business_config_id=BUSINESS_CONFIG_ID))

    assert result.linked is False
    assert result.live_mode is None
    assert result.user_id is None
    assert result.public_key is None


def test_reports_linked_account_details():
    repository = FakeMercadoPagoCredentialRepository(
        {BUSINESS_CONFIG_ID: make_credential()}
    )
    use_case = GetLinkStatusUseCase(repository)

    result = use_case.execute(GetLinkStatusQuery(business_config_id=BUSINESS_CONFIG_ID))

    assert result.linked is True
    assert result.live_mode is True
    assert result.user_id == "987654321"
    assert result.public_key == "APP_USR-public-key"


def test_never_exposes_tokens():
    fields = {field.name for field in dataclasses.fields(GetLinkStatusResult)}

    assert fields == {"linked", "live_mode", "user_id", "public_key"}


def test_a_different_business_is_not_linked():
    repository = FakeMercadoPagoCredentialRepository(
        {BUSINESS_CONFIG_ID: make_credential()}
    )
    use_case = GetLinkStatusUseCase(repository)

    result = use_case.execute(
        GetLinkStatusQuery(business_config_id=OTHER_BUSINESS_CONFIG_ID)
    )

    assert result.linked is False
