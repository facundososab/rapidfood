import pytest

from modules.mercadopago.domain.models.mercadopago_credential import (
    MercadoPagoCredential,
)

BUSINESS_CONFIG_ID = "11111111-1111-1111-1111-111111111111"


def test_create_normalizes_optional_fields_and_is_linked():
    credential = MercadoPagoCredential.create(
        business_config_id=f"  {BUSINESS_CONFIG_ID}  ",
        access_token="APP_USR-token",
        refresh_token="TG-refresh",
        user_id="987",
        public_key="APP_USR-public-key",
        live_mode=True,
    )

    assert credential.business_config_id == BUSINESS_CONFIG_ID
    assert credential.access_token == "APP_USR-token"
    assert credential.refresh_token == "TG-refresh"
    assert credential.user_id == "987"
    assert credential.public_key == "APP_USR-public-key"
    assert credential.live_mode is True
    assert credential.credential_id is None
    assert credential.is_linked is True


@pytest.mark.parametrize("business_config_id", ["", "   "])
def test_rejects_blank_business_config_id(business_config_id):
    with pytest.raises(ValueError, match="business_config_id"):
        MercadoPagoCredential.create(
            business_config_id=business_config_id,
            access_token="APP_USR-token",
        )


@pytest.mark.parametrize("access_token", ["", "   "])
def test_rejects_blank_access_token(access_token):
    with pytest.raises(ValueError, match="access_token"):
        MercadoPagoCredential.create(
            business_config_id=BUSINESS_CONFIG_ID,
            access_token=access_token,
        )
