"""REST views for business configuration."""

from __future__ import annotations

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.business.application.ports.driver.get_business_configuration_port import GetBusinessConfigurationQuery
from modules.business.application.ports.driver.save_business_configuration_port import SaveBusinessConfigurationCommand
from modules.business.application.ports.driver.upsert_business_hours_port import UpsertBusinessHoursCommand, BusinessHoursInput
from modules.business.application.ports.driver.create_address_port import CreateAddressCommand
from modules.business.application.ports.driver.delete_address_port import DeleteAddressCommand

from modules.business.domain.errors.business_errors import (
    AddressDoesNotBelongToBusinessError,
    AddressNotFoundError,
    BusinessConfigurationNotFoundError,
    InvalidBusinessHoursError,
)


def _get_container():
    from modules.business.configuration.container import get_business_container
    return get_business_container()


def _error(msg: str, code: int = 400) -> Response:
    return Response({"detail": msg}, status=code)


# ---- Serializers ----

class BusinessHoursInputSerializer(serializers.Serializer):
    VALID_DAYS = {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"}
    open_week_day = serializers.CharField()
    open_from_hour = serializers.RegexField(r"^\d{2}:\d{2}$")
    open_to_hour = serializers.RegexField(r"^\d{2}:\d{2}$")

    def validate_open_week_day(self, value):
        v = value.upper()
        if v not in self.VALID_DAYS:
            raise serializers.ValidationError(f"Invalid weekday: '{value}'")
        return v


class SaveBusinessSerializer(serializers.Serializer):
    business_name = serializers.CharField(max_length=255)
    min_order = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class AddressSerializer(serializers.Serializer):
    street = serializers.CharField(max_length=255)
    street_number = serializers.CharField(max_length=50)
    city = serializers.CharField(max_length=100)
    province = serializers.CharField(max_length=100)
    floor = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True, default=None)
    apartment = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True, default=None)
    postal_code = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True, default=None)


# ---- Views ----

class BusinessConfigurationView(APIView):
    """GET/PATCH /api/business/<business_config_id>/"""

    def get(self, request: Request, business_config_id: str) -> Response:
        try:
            result = _get_container().get_configuration.execute(
                GetBusinessConfigurationQuery(business_config_id=business_config_id)
            )
        except BusinessConfigurationNotFoundError as e:
            return _error(str(e), 404)
        return Response(result)

    def patch(self, request: Request, business_config_id: str) -> Response:
        s = SaveBusinessSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            result = _get_container().save_configuration.execute(
                SaveBusinessConfigurationCommand(
                    business_config_id=business_config_id,
                    business_name=d["business_name"],
                    min_order=d["min_order"],
                    shipping_cost=d["shipping_cost"],
                )
            )
        except BusinessConfigurationNotFoundError as e:
            return _error(str(e), 404)
        return Response(result)


class BusinessHoursView(APIView):
    """PUT /api/business/<business_config_id>/hours/"""

    def put(self, request: Request, business_config_id: str) -> Response:
        s = BusinessHoursInputSerializer(data=request.data, many=True)
        s.is_valid(raise_exception=True)
        hours = [
            BusinessHoursInput(
                open_week_day=item["open_week_day"],
                open_from_hour=item["open_from_hour"],
                open_to_hour=item["open_to_hour"],
            )
            for item in s.validated_data
        ]
        try:
            _get_container().upsert_hours.execute(
                UpsertBusinessHoursCommand(
                    business_config_id=business_config_id,
                    hours=hours,
                )
            )
        except (BusinessConfigurationNotFoundError, InvalidBusinessHoursError) as e:
            return _error(str(e), 400)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddressListView(APIView):
    """POST /api/business/<business_config_id>/addresses/"""

    def post(self, request: Request, business_config_id: str) -> Response:
        s = AddressSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        try:
            result = _get_container().create_address.execute(
                CreateAddressCommand(
                    business_config_id=business_config_id,
                    street=d["street"],
                    street_number=d["street_number"],
                    city=d["city"],
                    province=d["province"],
                    floor=d.get("floor"),
                    apartment=d.get("apartment"),
                    postal_code=d.get("postal_code"),
                )
            )
        except BusinessConfigurationNotFoundError as e:
            return _error(str(e), 404)
        return Response(result, status=status.HTTP_201_CREATED)


class AddressDetailView(APIView):
    """DELETE /api/business/<business_config_id>/addresses/<address_id>/"""

    def delete(self, request: Request, business_config_id: str, address_id: str) -> Response:
        try:
            _get_container().delete_address.execute(
                DeleteAddressCommand(
                    business_config_id=business_config_id,
                    address_id=address_id,
                )
            )
        except (AddressNotFoundError, AddressDoesNotBelongToBusinessError) as e:
            return _error(str(e), 404)
        return Response(status=status.HTTP_204_NO_CONTENT)
