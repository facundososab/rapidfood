"""Use case tests for CalculateDeliveryQuoteUseCase."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict

import pytest

from modules.delivery.application.ports.driver.calculate_delivery_quote_ports import (
    AddressInput,
    CalculateDeliveryQuoteCommand,
)
from modules.delivery.application.use_cases.calculate_delivery_quote_use_case import (
    CalculateDeliveryQuoteUseCase,
)
from modules.delivery.domain.errors.delivery_errors import (
    AddressCouldNotBeGeocodedError,
    BusinessConfigurationNotFoundError,
    DeliveryConfigurationNotFoundError,
    GeocodingProviderError,
    RoutingProviderError,
)
from modules.delivery.domain.models.coordinates import Coordinates
from modules.delivery.domain.models.delivery_configuration import DeliveryConfiguration
from modules.delivery.domain.models.delivery_pricing_config import DeliveryPricingConfig
from modules.delivery.domain.models.delivery_zone import DeliveryZone
from modules.delivery.domain.models.postal_address import PostalAddress
from modules.delivery.domain.models.week_day import WeekDay
from modules.delivery.domain.services.delivery_price_calculator import (
    DeliveryPriceCalculator,
)
from modules.delivery.tests.use_cases.fakes import (
    AlwaysOutsideGeometryPort,
    AlwaysValidGeometryPort,
    ErrorGeocodingPort,
    FailingGeocodingPort,
    FailingRoutingPort,
    FixedClock,
    FixedDemandPort,
    FixedGeocodingPort,
    FixedRoutingPort,
    InMemoryDeliveryConfigurationRepository,
)

# Monday noon UTC (isoweekday = 0 = MONDAY)
_MONDAY_NOON = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)

_BIZ_ID = "biz-001"
_ADDR_ID = "addr-001"

_ALL_WEEKDAYS_ONE = {day: Decimal("1.00") for day in WeekDay}


def _pricing_config(**overrides) -> DeliveryPricingConfig:
    defaults = dict(
        price_per_km=Decimal("10.00"),
        high_demand_threshold=5,
        very_high_demand_threshold=10,
        high_demand_multiplier=Decimal("1.50"),
        very_high_demand_multiplier=Decimal("2.00"),
        weekday_multipliers={**_ALL_WEEKDAYS_ONE},
    )
    defaults.update(overrides)
    return DeliveryPricingConfig(**defaults)


def _zone() -> DeliveryZone:
    return DeliveryZone(
        exterior_ring=[
            Coordinates(0.0, 0.0),
            Coordinates(1.0, 0.0),
            Coordinates(1.0, 1.0),
            Coordinates(0.0, 0.0),
        ]
    )


def _origin_address() -> PostalAddress:
    return PostalAddress(street="Av. Corrientes", street_number="1234", city="CABA", province="Buenos Aires")


def _dest_input() -> AddressInput:
    return AddressInput(
        street="Av. Rivadavia",
        street_number="5678",
        city="CABA",
        province="Buenos Aires",
    )


def _command(biz_id: str = _BIZ_ID) -> CalculateDeliveryQuoteCommand:
    return CalculateDeliveryQuoteCommand(
        business_config_id=biz_id,
        destination_address=_dest_input(),
    )


def _configured_delivery() -> DeliveryConfiguration:
    return DeliveryConfiguration(
        business_config_id=_BIZ_ID,
        base_shipping_cost=Decimal("50.00"),
        origin_address_id=_ADDR_ID,
        origin_address=_origin_address(),
        delivery_zone=_zone(),
        pricing_config=_pricing_config(),
    )


def _make_uc(
    repo=None,
    geocoding=None,
    geometry=None,
    routing=None,
    demand=None,
    clock=None,
):
    return CalculateDeliveryQuoteUseCase(
        delivery_config_repo=repo or InMemoryDeliveryConfigurationRepository(),
        geocoding=geocoding or FixedGeocodingPort(Coordinates(0.5, 0.5)),
        geometry=geometry or AlwaysValidGeometryPort(),
        routing=routing or FixedRoutingPort(distance_km=3.0, duration_minutes=10.0),
        demand_provider=demand or FixedDemandPort(0),
        clock=clock or FixedClock(_MONDAY_NOON),
        price_calculator=DeliveryPriceCalculator(),
    )


class TestConfigurationNotFound:
    def test_raises_when_business_not_configured(self):
        uc = _make_uc()
        with pytest.raises(BusinessConfigurationNotFoundError):
            uc.execute(_command())


class TestDeliveryConfigurationNotComplete:
    def test_raises_when_zone_not_configured(self):
        repo = InMemoryDeliveryConfigurationRepository()
        config = DeliveryConfiguration(
            business_config_id=_BIZ_ID,
            base_shipping_cost=Decimal("50.00"),
            origin_address_id=_ADDR_ID,
            origin_address=_origin_address(),
            delivery_zone=None,
            pricing_config=_pricing_config(),
        )
        repo.save(config)
        uc = _make_uc(repo=repo)
        with pytest.raises(DeliveryConfigurationNotFoundError):
            uc.execute(_command())

    def test_raises_when_pricing_not_configured(self):
        repo = InMemoryDeliveryConfigurationRepository()
        config = DeliveryConfiguration(
            business_config_id=_BIZ_ID,
            base_shipping_cost=Decimal("50.00"),
            origin_address_id=_ADDR_ID,
            origin_address=_origin_address(),
            delivery_zone=_zone(),
            pricing_config=None,
        )
        repo.save(config)
        uc = _make_uc(repo=repo)
        with pytest.raises(DeliveryConfigurationNotFoundError):
            uc.execute(_command())


class TestOutsideZone:
    def test_returns_unavailable_when_destination_outside_zone(self):
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(repo=repo, geometry=AlwaysOutsideGeometryPort())
        result = uc.execute(_command())
        assert result.available is False
        assert result.shipping_cost is None

    def test_routing_not_called_when_outside(self):
        """Routing must NOT be called when destination is outside the zone."""
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(
            repo=repo,
            geometry=AlwaysOutsideGeometryPort(),
            routing=FailingRoutingPort(),  # would raise if called
        )
        # Should NOT raise RoutingProviderError
        result = uc.execute(_command())
        assert result.available is False


class TestInsideZone:
    def test_returns_available_with_cost(self):
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(
            repo=repo,
            routing=FixedRoutingPort(distance_km=5.0, duration_minutes=15.0),
            demand=FixedDemandPort(0),  # NORMAL demand
            clock=FixedClock(_MONDAY_NOON),
        )
        result = uc.execute(_command())
        assert result.available is True
        assert result.distance_km == 5.0
        assert result.estimated_duration_minutes == 15.0
        # base=50 + 5km*10/km = 100, *1.00 (weekday MONDAY) *1.00 (NORMAL) = 100.00
        assert result.shipping_cost == Decimal("100.00")
        assert result.demand_level == "NORMAL"

    def test_high_demand_surcharge(self):
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(
            repo=repo,
            routing=FixedRoutingPort(distance_km=0.0, duration_minutes=0.0),
            demand=FixedDemandPort(5),  # HIGH demand (threshold=5)
            clock=FixedClock(_MONDAY_NOON),
        )
        result = uc.execute(_command())
        assert result.available is True
        assert result.demand_level == "HIGH"
        # base=50, *1.50 demand = 75.00
        assert result.shipping_cost == Decimal("75.00")

    def test_very_high_demand_surcharge(self):
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(
            repo=repo,
            routing=FixedRoutingPort(distance_km=0.0, duration_minutes=0.0),
            demand=FixedDemandPort(10),  # VERY_HIGH demand (threshold=10)
            clock=FixedClock(_MONDAY_NOON),
        )
        result = uc.execute(_command())
        assert result.demand_level == "VERY_HIGH"
        # base=50, *2.00 demand = 100.00
        assert result.shipping_cost == Decimal("100.00")


class TestGeocodingFailure:
    def test_raises_when_geocoding_fails_with_no_result(self):
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(repo=repo, geocoding=FailingGeocodingPort())
        with pytest.raises(AddressCouldNotBeGeocodedError):
            uc.execute(_command())

    def test_raises_when_geocoding_provider_errors(self):
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(repo=repo, geocoding=ErrorGeocodingPort())
        with pytest.raises(GeocodingProviderError):
            uc.execute(_command())


class TestRoutingFailure:
    def test_raises_when_routing_fails(self):
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_configured_delivery())
        uc = _make_uc(repo=repo, routing=FailingRoutingPort())
        with pytest.raises(RoutingProviderError):
            uc.execute(_command())
