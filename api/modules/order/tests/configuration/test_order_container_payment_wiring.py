from modules.order.application.use_cases.create_payment_checkout_use_case import (
    CreatePaymentCheckoutUseCase,
)
from modules.order.application.use_cases.handle_payment_webhook_use_case import (
    HandlePaymentWebhookUseCase,
)
from modules.order.application.use_cases.cancel_superseded_checkout_use_case import (
    CancelSupersededCheckoutUseCase,
)
from modules.order.configuration.container import OrderContainer
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_payment_provider import (
    MercadoPagoPaymentProvider,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_settings import (
    MercadoPagoSettings,
)
from modules.order.infrastructure.adapters.driven.prisma.payment_repository import (
    PrismaPaymentRepository,
)


def test_order_container_wires_payment_dependencies_explicitly(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "test-token")
    prisma_client = object()

    container = OrderContainer(prisma_client=prisma_client)

    assert isinstance(container.payment_repository, PrismaPaymentRepository)
    assert container.payment_repository._prisma is prisma_client
    assert isinstance(container.mercadopago_settings, MercadoPagoSettings)
    assert container.mercadopago_settings.currency == "ARS"
    assert isinstance(container.payment_provider, MercadoPagoPaymentProvider)
    assert container.payment_provider.settings is container.mercadopago_settings

    assert isinstance(container.create_payment_checkout_use_case, CreatePaymentCheckoutUseCase)
    assert container.create_payment_checkout_use_case._order_repo is container.order_repository
    assert container.create_payment_checkout_use_case._payment_repo is container.payment_repository
    assert container.create_payment_checkout_use_case._payment_provider is container.payment_provider
    assert container.create_payment_checkout_use_case._currency == "ARS"

    assert isinstance(
        container.handle_payment_webhook_use_case,
        HandlePaymentWebhookUseCase,
    )
    assert container.handle_payment_webhook_use_case._order_repo is container.order_repository
    assert container.handle_payment_webhook_use_case._payment_repo is container.payment_repository
    assert (
        container.handle_payment_webhook_use_case._payment_provider
        is container.payment_provider
    )

    assert isinstance(
        container.cancel_superseded_checkout_use_case,
        CancelSupersededCheckoutUseCase,
    )
    assert (
        container.cancel_superseded_checkout_use_case._payment_repo
        is container.payment_repository
    )


def test_order_container_propagates_the_credentials_query(monkeypatch):
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "test-token")
    credentials_query = object()

    container = OrderContainer(
        prisma_client=object(), credentials_query=credentials_query
    )

    assert container.credentials_query is credentials_query
    assert (
        container.create_payment_checkout_use_case._credentials_query
        is credentials_query
    )
    assert (
        container.handle_payment_webhook_use_case._credentials_query
        is credentials_query
    )
