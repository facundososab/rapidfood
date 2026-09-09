from modules.order.application.use_cases.create_payment_link_use_case import (
    CreatePaymentLinkUseCase,
)
from modules.order.application.use_cases.process_payment_notification_use_case import (
    ProcessPaymentNotificationUseCase,
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

    assert isinstance(container.create_payment_link_use_case, CreatePaymentLinkUseCase)
    assert container.create_payment_link_use_case.order_repo is container.order_repository
    assert container.create_payment_link_use_case.payment_repo is container.payment_repository
    assert container.create_payment_link_use_case.payment_provider is container.payment_provider
    assert container.create_payment_link_use_case.currency == "ARS"

    assert isinstance(
        container.process_payment_notification_use_case,
        ProcessPaymentNotificationUseCase,
    )
    assert container.process_payment_notification_use_case.order_repo is container.order_repository
    assert container.process_payment_notification_use_case.payment_repo is container.payment_repository
    assert (
        container.process_payment_notification_use_case.payment_provider
        is container.payment_provider
    )
