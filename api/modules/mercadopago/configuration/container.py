"""Composition root for the Mercado Pago linkage module.

Standalone by design: it wires only its own adapters, so the module can be
imported by the REST driver without pulling in ``order`` or any other context.
"""

from functools import lru_cache

from modules.mercadopago.application.ports.driven.mercadopago_credential_repository import (
    MercadoPagoCredentialRepositoryPort,
)
from modules.mercadopago.application.ports.driven.mercadopago_oauth_client import (
    MercadoPagoOAuthClientPort,
)
from modules.mercadopago.application.ports.driven.mercadopago_state_signer import (
    MercadoPagoStateSignerPort,
)
from modules.mercadopago.application.use_cases.build_authorization_url_use_case import (
    BuildAuthorizationUrlUseCase,
)
from modules.mercadopago.application.use_cases.get_link_status_use_case import (
    GetLinkStatusUseCase,
)
from modules.mercadopago.application.use_cases.get_mercadopago_access_token_use_case import (
    GetMercadoPagoAccessTokenUseCase,
)
from modules.mercadopago.application.use_cases.link_mercadopago_account_use_case import (
    LinkMercadoPagoAccountUseCase,
)
from modules.mercadopago.application.use_cases.unlink_mercadopago_account_use_case import (
    UnlinkMercadoPagoAccountUseCase,
)
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_oauth_client import (
    MercadoPagoOAuthClient,
    MercadoPagoOAuthSettings,
)
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_state_signer import (
    DjangoStateSigner,
)
from modules.mercadopago.infrastructure.adapters.driven.prisma.mercadopago_credential_repository import (
    PrismaMercadoPagoCredentialRepository,
)


class MercadoPagoContainer:
    def __init__(
        self,
        settings: MercadoPagoOAuthSettings | None = None,
        repository: MercadoPagoCredentialRepositoryPort | None = None,
        oauth_client: MercadoPagoOAuthClientPort | None = None,
        state_signer: MercadoPagoStateSignerPort | None = None,
    ) -> None:
        settings = settings if settings is not None else MercadoPagoOAuthSettings.from_env()
        repository = (
            repository
            if repository is not None
            else PrismaMercadoPagoCredentialRepository()
        )
        oauth_client = (
            oauth_client if oauth_client is not None else MercadoPagoOAuthClient(settings)
        )
        state_signer = state_signer if state_signer is not None else DjangoStateSigner()

        # Exposed so the REST driver can read presentation-only settings (e.g.
        # where to send the browser back after the OAuth round trip) without
        # importing the settings dataclass itself.
        self.settings = settings

        self.build_authorization_url = BuildAuthorizationUrlUseCase(
            oauth_client,
            state_signer,
        )
        self.link_account = LinkMercadoPagoAccountUseCase(
            repository,
            oauth_client,
            state_signer,
        )
        self.get_link_status = GetLinkStatusUseCase(repository)
        self.get_access_token = GetMercadoPagoAccessTokenUseCase(repository)
        self.unlink_account = UnlinkMercadoPagoAccountUseCase(repository)


@lru_cache(maxsize=1)
def get_mercadopago_container() -> MercadoPagoContainer:
    return MercadoPagoContainer()
