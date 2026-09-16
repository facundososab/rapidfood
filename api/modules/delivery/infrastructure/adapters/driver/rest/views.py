"""DRF views for the delivery REST inbound adapter.

Views parse HTTP, validate format via serializers, translate to commands,
call the inbound port (use case) obtained from the composition root, and
translate domain errors to HTTP codes. NO business rules here.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.delivery.application.ports.driver.calculate_delivery_quote_ports import (
    AddressInput,
    CalculateDeliveryQuoteCommand,
)
from modules.delivery.application.ports.driver.configure_delivery_ports import (
    ConfigureDeliveryCommand,
    CoordinateInput,
    DeliveryZoneInput,
    WeekdayMultiplierInput,
)
from modules.delivery.application.ports.driver.get_delivery_configuration_ports import (
    GetDeliveryConfigurationQuery,
)
from modules.delivery.domain.errors.delivery_errors import (
    AddressCouldNotBeGeocodedError,
    BusinessConfigurationNotFoundError,
    DeliveryConfigurationNotFoundError,
    DeliveryDomainError,
    DeliveryOriginDoesNotBelongToBusinessError,
    DeliveryOriginNotConfiguredError,
    GeocodingProviderError,
    InvalidDeliveryPricingConfigurationError,
    InvalidDeliveryZoneError,
    RoutingProviderError,
)
from modules.delivery.infrastructure.adapters.driver.rest.serializers import (
    CalculateDeliveryQuoteSerializer,
    ConfigureDeliverySerializer,
)


def _domain_error_to_response(error: DeliveryDomainError) -> Response:
    """Map domain errors to appropriate HTTP status codes."""
    if isinstance(error, BusinessConfigurationNotFoundError):
        return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(error, DeliveryConfigurationNotFoundError):
        return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(error, (
        InvalidDeliveryZoneError,
        InvalidDeliveryPricingConfigurationError,
        DeliveryOriginNotConfiguredError,
        DeliveryOriginDoesNotBelongToBusinessError,
        AddressCouldNotBeGeocodedError,
    )):
        return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(error, (GeocodingProviderError, RoutingProviderError)):
        return Response(
            {"detail": "A geographic service is temporarily unavailable. Please retry."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    # Fallback for any other domain error
    return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)


class DeliveryConfigurationView(APIView):
    """Retrieve or configure delivery settings for a restaurant.

    URL: GET/POST /api/delivery/{business_config_id}/configure/

    A single view serves both methods so the route is registered once.
    (Two separate views on the same path made the GET view shadow the
    POST view, returning 405 on every save.)
    """

    get_delivery_configuration = None  # injected by the container
    configure_delivery = None  # injected by the container

    def get(self, request: Request, business_config_id: str) -> Response:
        query = GetDeliveryConfigurationQuery(
            business_config_id=str(business_config_id)
        )
        try:
            result = self.get_delivery_configuration.execute(query)
        except DeliveryDomainError as exc:
            return _domain_error_to_response(exc)

        return Response(
            {
                "business_config_id": result.business_config_id,
                "base_shipping_cost": (
                    str(result.base_shipping_cost)
                    if result.base_shipping_cost else None
                ),
                "origin_address_id": result.origin_address_id,
                "available_zone": result.available_zone,
                "price_per_km": str(result.price_per_km) if result.price_per_km else None,
                "high_demand_threshold": result.high_demand_threshold,
                "very_high_demand_threshold": result.very_high_demand_threshold,
                "high_demand_multiplier": (
                    str(result.high_demand_multiplier)
                    if result.high_demand_multiplier else None
                ),
                "very_high_demand_multiplier": (
                    str(result.very_high_demand_multiplier)
                    if result.very_high_demand_multiplier else None
                ),
                "weekday_multipliers": [
                    {
                        "week_day": wm.week_day,
                        "multiplier": str(wm.multiplier),
                    }
                    for wm in result.weekday_multipliers
                ],
                "is_configured": result.is_configured,
            }
        )

    def post(self, request: Request, business_config_id: str) -> Response:
        serializer = ConfigureDeliverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        zone_data = data["delivery_zone"]
        exterior_ring = [
            CoordinateInput(longitude=c["longitude"], latitude=c["latitude"])
            for c in zone_data["exterior_ring"]
        ]
        holes = [
            [
                CoordinateInput(longitude=c["longitude"], latitude=c["latitude"])
                for c in ring
            ]
            for ring in zone_data.get("holes", [])
        ]

        weekday_multipliers = [
            WeekdayMultiplierInput(
                week_day=entry["week_day"],
                multiplier=entry["multiplier"],
            )
            for entry in data["weekday_multipliers"]
        ]

        command = ConfigureDeliveryCommand(
            business_config_id=str(business_config_id),
            base_shipping_cost=data["base_shipping_cost"],
            origin_address_id=str(data["origin_address_id"]),
            delivery_zone=DeliveryZoneInput(
                exterior_ring=exterior_ring,
                holes=holes,
            ),
            price_per_km=data["price_per_km"],
            high_demand_threshold=data["high_demand_threshold"],
            very_high_demand_threshold=data["very_high_demand_threshold"],
            high_demand_multiplier=data["high_demand_multiplier"],
            very_high_demand_multiplier=data["very_high_demand_multiplier"],
            weekday_multipliers=weekday_multipliers,
        )

        try:
            result = self.configure_delivery.execute(command)
        except DeliveryDomainError as exc:
            return _domain_error_to_response(exc)

        return Response(
            {"business_config_id": result.business_config_id},
            status=status.HTTP_200_OK,
        )


class CalculateDeliveryQuoteView(APIView):
    """Calculate a delivery quote for a customer destination.

    URL: POST /api/delivery/{business_config_id}/quote/
    """

    calculate_delivery_quote = None  # injected by the container

    def post(self, request: Request, business_config_id: str) -> Response:
        serializer = CalculateDeliveryQuoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        dest = data["destination_address"]

        command = CalculateDeliveryQuoteCommand(
            business_config_id=str(business_config_id),
            destination_address=AddressInput(
                street=dest["street"],
                street_number=dest["street_number"],
                city=dest["city"],
                province=dest["province"],
                floor=dest.get("floor"),
                apartment=dest.get("apartment"),
                postal_code=dest.get("postal_code"),
            ),
        )

        try:
            result = self.calculate_delivery_quote.execute(command)
        except DeliveryDomainError as exc:
            return _domain_error_to_response(exc)

        response_data = {"available": result.available}
        if result.available:
            response_data.update(
                {
                    "distance_km": result.distance_km,
                    "estimated_duration_minutes": result.estimated_duration_minutes,
                    "shipping_cost": str(result.shipping_cost),
                    "demand_level": result.demand_level,
                }
            )
        return Response(response_data)
