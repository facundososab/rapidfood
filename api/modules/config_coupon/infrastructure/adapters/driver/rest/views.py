"""DRF views for the coupon REST adapter.

Views parse HTTP, validate format via serializers, translate to commands, call
the inbound port (use case) obtained from the composition root, and translate
domain errors to HTTP codes. NO business rules here.

Only the ADMIN surface is exposed over REST (create / list / get-by-code /
toggle). The cross-module operations (validate / consume) are consumed
in-process by the order module through the application ports — never over HTTP.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.config_coupon.application.ports.driver.coupon_admin_ports import (
    CreateCouponCommand,
    GetCouponByCodeQuery,
    ListCouponsQuery,
    ToggleCouponStatusCommand,
)
from modules.config_coupon.domain.errors.coupon_errors import (
    CouponAlreadyExistsError,
    CouponNotFoundError,
    DomainError,
)
from modules.config_coupon.infrastructure.adapters.driver.rest.serializers import (
    CreateCouponSerializer,
    ToggleCouponStatusSerializer,
)


def _error_response(error: DomainError) -> Response:
    """Translate a domain error to the appropriate HTTP status code."""
    if isinstance(error, CouponNotFoundError):
        return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(error, CouponAlreadyExistsError):
        return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)
    return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class CreateCouponView(APIView):
    create_coupon = None  # injected by the container

    def post(self, request: Request) -> Response:
        serializer = CreateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = self.create_coupon.execute(
                CreateCouponCommand(
                    coupon_code=data["coupon_code"],
                    coupon_type=data["coupon_type"],
                    amount=data["amount"],
                    available_uses=data["available_uses"],
                    min_order_amount=data.get("min_order_amount"),
                    date_of_expiration=data.get("date_of_expiration"),
                    is_active=data.get("is_active", True),
                )
            )
        except DomainError as exc:
            return _error_response(exc)
        return Response(
            {
                "coupon_id": result.coupon_id,
                "coupon_code": result.coupon_code,
                "coupon_type": result.coupon_type,
                "amount": str(result.amount),
                "available_uses": result.available_uses,
                "min_order_amount": (
                    str(result.min_order_amount)
                    if result.min_order_amount is not None
                    else None
                ),
                "date_of_expiration": result.date_of_expiration,
                "is_active": result.is_active,
            },
            status=status.HTTP_201_CREATED,
        )


class ListCouponsView(APIView):
    list_coupons = None  # injected by the container

    def get(self, request: Request) -> Response:
        result = self.list_coupons.execute(ListCouponsQuery())
        return Response(
            [
                {
                    "coupon_id": coupon.coupon_id,
                    "coupon_code": coupon.coupon_code,
                    "coupon_type": coupon.coupon_type,
                    "amount": str(coupon.amount),
                    "available_uses": coupon.available_uses,
                    "min_order_amount": (
                        str(coupon.min_order_amount)
                        if coupon.min_order_amount is not None
                        else None
                    ),
                    "date_of_expiration": coupon.date_of_expiration,
                    "is_active": coupon.is_active,
                }
                for coupon in result.coupons
            ]
        )


class GetCouponByCodeView(APIView):
    get_coupon_by_code = None  # injected by the container

    def get(self, request: Request, coupon_code: str) -> Response:
        try:
            result = self.get_coupon_by_code.execute(
                GetCouponByCodeQuery(coupon_code=coupon_code)
            )
        except DomainError as exc:
            return _error_response(exc)
        return Response(
            {
                "coupon_id": result.coupon_id,
                "coupon_code": result.coupon_code,
                "coupon_type": result.coupon_type,
                "amount": str(result.amount),
                "available_uses": result.available_uses,
                "min_order_amount": (
                    str(result.min_order_amount)
                    if result.min_order_amount is not None
                    else None
                ),
                "date_of_expiration": result.date_of_expiration,
                "is_active": result.is_active,
            }
        )


class ToggleCouponStatusView(APIView):
    toggle_coupon_status = None  # injected by the container

    def patch(self, request: Request, coupon_id: str) -> Response:
        serializer = ToggleCouponStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = self.toggle_coupon_status.execute(
                ToggleCouponStatusCommand(
                    coupon_id=coupon_id,
                    is_active=serializer.validated_data["is_active"],
                )
            )
        except DomainError as exc:
            return _error_response(exc)
        return Response(
            {"coupon_id": result.coupon_id, "is_active": result.is_active}
        )
