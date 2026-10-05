"""Link a Mercado Pago account to a business.

Order of operations matters: the state is validated BEFORE the code is
exchanged, so a forged callback can never reach Mercado Pago, and the network
call happens outside any database transaction. The PKCE ``code_verifier``
proves possession of the secret that produced the ``code_challenge`` of the
original authorization request.
"""

from modules.mercadopago.application.ports.driven.mercadopago_credential_repository import (
    MercadoPagoCredentialRepositoryPort,
)
from modules.mercadopago.application.ports.driven.mercadopago_oauth_client import (
    MercadoPagoOAuthClientPort,
)
from modules.mercadopago.application.ports.driven.mercadopago_state_signer import (
    MercadoPagoStateSignerPort,
)
from modules.mercadopago.application.ports.driver.link_mercadopago_account_port import (
    LinkMercadoPagoAccountCommand,
    LinkMercadoPagoAccountResult,
)
from modules.mercadopago.domain.models.mercadopago_credential import (
    MercadoPagoCredential,
)


class LinkMercadoPagoAccountUseCase:
    def __init__(
        self,
        repository: MercadoPagoCredentialRepositoryPort,
        oauth_client: MercadoPagoOAuthClientPort,
        state_signer: MercadoPagoStateSignerPort,
    ) -> None:
        self._repository = repository
        self._oauth_client = oauth_client
        self._state_signer = state_signer

    def execute(
        self,
        command: LinkMercadoPagoAccountCommand,
    ) -> LinkMercadoPagoAccountResult:
        signed = self._state_signer.unsign(command.state)

        tokens = self._oauth_client.exchange_code(
            command.code,
            command.redirect_uri,
            code_verifier=signed.code_verifier,
        )

        credential = self._repository.upsert(
            MercadoPagoCredential.create(
                business_config_id=signed.business_config_id,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                user_id=tokens.user_id,
                public_key=tokens.public_key,
                live_mode=tokens.live_mode,
            )
        )

        return LinkMercadoPagoAccountResult(
            credential_id=credential.credential_id,
            business_config_id=credential.business_config_id,
            live_mode=credential.live_mode,
            user_id=credential.user_id,
        )
