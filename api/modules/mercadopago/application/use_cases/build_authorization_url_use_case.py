"""Build the Mercado Pago authorization URL for a business.

The use case asks the OAuth client for a PKCE pair, seals the verifier inside
the signed ``state`` (the callback needs it to exchange the code), and delegates
URL construction to the OAuth client, which owns the application credentials.
"""

from modules.mercadopago.application.ports.driven.mercadopago_oauth_client import (
    MercadoPagoOAuthClientPort,
)
from modules.mercadopago.application.ports.driven.mercadopago_state_signer import (
    MercadoPagoStateSignerPort,
)
from modules.mercadopago.application.ports.driver.build_authorization_url_port import (
    BuildAuthorizationUrlCommand,
    BuildAuthorizationUrlResult,
)


class BuildAuthorizationUrlUseCase:
    def __init__(
        self,
        oauth_client: MercadoPagoOAuthClientPort,
        state_signer: MercadoPagoStateSignerPort,
    ) -> None:
        self._oauth_client = oauth_client
        self._state_signer = state_signer

    def execute(
        self,
        command: BuildAuthorizationUrlCommand,
    ) -> BuildAuthorizationUrlResult:
        verifier, challenge = self._oauth_client.generate_pkce_pair()
        state = self._state_signer.sign(
            command.business_config_id,
            code_verifier=verifier,
        )
        authorization_url = self._oauth_client.build_authorization_url(
            state,
            code_challenge=challenge,
        )
        return BuildAuthorizationUrlResult(authorization_url=authorization_url)
