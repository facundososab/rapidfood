"""REST driver adapter: the "Connect your Mercado Pago account" endpoints.

Views only translate HTTP <-> commands and map domain errors to status codes;
every rule lives in a use case. The wiring root is resolved from ``composition``
(the app-level composition root), like the staff and order views do, so a driver
adapter never imports a driven adapter directly.

Mercado Pago sends the payer's browser back to the callback with no JWT and no
panel context: when ``MERCADOPAGO_RETURN_URI`` is configured the callback answers
with a redirect to the panel (``?mp=linked`` / ``?mp=error``) so a human sees a
page instead of raw JSON. Without it, the JSON contract is preserved.
"""

from __future__ import annotations

import logging

from django.http import HttpResponseRedirect
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from composition.container import get_app_mercadopago_container
from modules.mercadopago.application.ports.driver.build_authorization_url_port import (
    BuildAuthorizationUrlCommand,
)
from modules.mercadopago.application.ports.driver.get_link_status_port import (
    GetLinkStatusQuery,
)
from modules.mercadopago.application.ports.driver.link_mercadopago_account_port import (
    LinkMercadoPagoAccountCommand,
)
from modules.mercadopago.application.ports.driver.unlink_mercadopago_account_port import (
    UnlinkMercadoPagoAccountCommand,
)
from modules.mercadopago.domain.errors.mercadopago_errors import (
    MercadoPagoConfigurationError,
    MercadoPagoOAuthError,
    MercadoPagoStateError,
)


def _error(message: str, code: int) -> Response:
    return Response({"error": message}, status=code)


def _redirect_to_panel(return_uri: str, outcome: str) -> HttpResponseRedirect:
    """Send the browser back to the panel with the outcome of the round trip."""
    return HttpResponseRedirect(f"{return_uri.rstrip('/')}?mp={outcome}")


class BusinessConfigIdSerializer(serializers.Serializer):
    """Validates the business id and normalizes it to its string form."""

    business_config_id = serializers.UUIDField()

    def validate_business_config_id(self, value) -> str:
        return str(value)


class OAuthCallbackSerializer(serializers.Serializer):
    code = serializers.CharField()
    state = serializers.CharField()
    redirect_uri = serializers.CharField(required=False, allow_blank=True, default=None)


class MercadoPagoAuthorizeView(APIView):
    """POST /api/mercadopago/authorize/ — URL the panel opens to connect an account.

    A missing OAuth application configuration is a deployment problem, hence
    503 instead of a client-side 400.
    """

    def post(self, request: Request) -> Response:
        serializer = BusinessConfigIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = get_app_mercadopago_container().build_authorization_url.execute(
                BuildAuthorizationUrlCommand(**serializer.validated_data)
            )
        except MercadoPagoConfigurationError as error:
            return _error(str(error), status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            {"authorization_url": result.authorization_url},
            status=status.HTTP_200_OK,
        )


class MercadoPagoCallbackView(APIView):
    """GET /api/mercadopago/callback/ — where Mercado Pago sends the browser.

    Public on purpose: the redirect carries no JWT. The signed ``state`` is the
    only thing that proves which business started the flow.
    """

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = OAuthCallbackSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        container = get_app_mercadopago_container()
        return_uri = container.settings.return_uri
        try:
            result = container.link_account.execute(
                LinkMercadoPagoAccountCommand(
                    code=serializer.validated_data["code"],
                    state=serializer.validated_data["state"],
                    redirect_uri=serializer.validated_data.get("redirect_uri") or None,
                )
            )
        except MercadoPagoStateError as error:
            logging.getLogger(__name__).warning(
                "MP callback state error: %s", error,
            )
            if return_uri:
                return _redirect_to_panel(return_uri, "error")
            return _error(str(error), status.HTTP_400_BAD_REQUEST)
        except MercadoPagoOAuthError as error:
            logging.getLogger(__name__).warning(
                "MP callback OAuth error: %s", error,
            )
            if return_uri:
                return _redirect_to_panel(return_uri, "error")
            return _error(str(error), status.HTTP_502_BAD_GATEWAY)
        except MercadoPagoConfigurationError as error:
            return _error(str(error), status.HTTP_503_SERVICE_UNAVAILABLE)
        if return_uri:
            return _redirect_to_panel(return_uri, "linked")
        return Response(
            {
                "linked": True,
                "business_config_id": result.business_config_id,
                "live_mode": result.live_mode,
            },
            status=status.HTTP_200_OK,
        )


class MercadoPagoStatusView(APIView):
    """GET /api/mercadopago/status/?business_config_id=<uuid> — token-free status."""

    def get(self, request: Request) -> Response:
        serializer = BusinessConfigIdSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        result = get_app_mercadopago_container().get_link_status.execute(
            GetLinkStatusQuery(**serializer.validated_data)
        )
        return Response(
            {
                "linked": result.linked,
                "live_mode": result.live_mode,
                "user_id": result.user_id,
                "public_key": result.public_key,
            },
            status=status.HTTP_200_OK,
        )


class MercadoPagoUnlinkView(APIView):
    """POST /api/mercadopago/unlink/ — idempotent disconnect."""

    def post(self, request: Request) -> Response:
        serializer = BusinessConfigIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        get_app_mercadopago_container().unlink_account.execute(
            UnlinkMercadoPagoAccountCommand(**serializer.validated_data)
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
