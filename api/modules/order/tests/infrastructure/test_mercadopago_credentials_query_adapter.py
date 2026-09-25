"""Tests for the cross-module Mercado Pago credentials adapter.

The adapter is the only order-side bridge to the linkage module, so it must
answer with a plain token and degrade to ``None`` instead of leaking linkage
failures into the payment flow.
"""

from modules.mercadopago.application.ports.driver.get_mercadopago_access_token_port import (
    GetMercadoPagoAccessTokenQuery,
)
from modules.order.infrastructure.adapters.driven.mercadopago.mercadopago_credentials_query_adapter import (
    MercadoPagoCredentialsQueryAdapter,
)


class FakeGetAccessTokenUseCase:
    def __init__(self, token=None, error=None):
        self.token = token
        self.error = error
        self.queries = []

    def execute(self, query):
        self.queries.append(query)
        if self.error is not None:
            raise self.error
        return self.token


def test_maps_the_business_id_to_the_linkage_query():
    use_case = FakeGetAccessTokenUseCase(token="APP_USR-business-token")
    adapter = MercadoPagoCredentialsQueryAdapter(use_case)

    token = adapter.get_access_token("biz-1")

    assert token == "APP_USR-business-token"
    assert use_case.queries == [GetMercadoPagoAccessTokenQuery(business_config_id="biz-1")]


def test_returns_none_when_the_business_is_unlinked():
    adapter = MercadoPagoCredentialsQueryAdapter(FakeGetAccessTokenUseCase())

    assert adapter.get_access_token("biz-1") is None


def test_degrades_to_none_when_the_linkage_module_fails():
    adapter = MercadoPagoCredentialsQueryAdapter(
        FakeGetAccessTokenUseCase(error=RuntimeError("linkage down"))
    )

    assert adapter.get_access_token("biz-1") is None
