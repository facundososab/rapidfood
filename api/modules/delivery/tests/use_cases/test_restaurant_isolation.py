"""Restaurant isolation test.

Verifies that two restaurants with different configurations produce
independent quotes — demand, pricing, and zone are fully isolated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from modules.delivery.application.ports.driver.calculate_delivery_quote_ports import (
    AddressInput,
    CalculateDeliveryQuoteCommand,
)
from modules.delivery.application.use_cases.calculate_delivery_quote_use_case import (
    CalculateDeliveryQuoteUseCase,
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
    AlwaysValidGeometryPort,
    FixedClock,
    FixedGeocodingPort,
    FixedRoutingPort,
    InMemoryDeliveryConfigurationRepository,
    PerBusinessDemandPort,
)

_MONDAY_NOON = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
_ALL_WEEKDAYS_ONE = {day: Decimal("1.00") for day in WeekDay}


def _make_zone() -> DeliveryZone:
    return DeliveryZone(
        exterior_ring=[
            Coordinates(0.0, 0.0),
            Coordinates(1.0, 0.0),
            Coordinates(1.0, 1.0),
            Coordinates(0.0, 0.0),
        ]
    )


def _make_config(biz_id: str, price_per_km: Decimal, base: Decimal) -> DeliveryConfiguration:
    return DeliveryConfiguration(
        business_config_id=biz_id,
        base_shipping_cost=base,
        origin_address_id="addr-" + biz_id,
        origin_address=PostalAddress(street="A", street_number="1", city="B", province="C"),
        delivery_zone=_make_zone(),
        pricing_config=DeliveryPricingConfig(
            price_per_km=price_per_km,
            high_demand_threshold=5,
            very_high_demand_threshold=10,
            high_demand_multiplier=Decimal("1.50"),
            very_high_demand_multiplier=Decimal("2.00"),
            weekday_multipliers={**_ALL_WEEKDAYS_ONE},
        ),
    )


class TestRestaurantIsolation:
    def test_different_configs_produce_independent_quotes(self):
        """Two restaurants: biz-A has 5km/10 per km; biz-B has 0km/20 per km."""
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_make_config("biz-A", price_per_km=Decimal("10.00"), base=Decimal("0.00")))
        repo.save(_make_config("biz-B", price_per_km=Decimal("20.00"), base=Decimal("0.00")))

        uc = CalculateDeliveryQuoteUseCase(
            delivery_config_repo=repo,
            geocoding=FixedGeocodingPort(Coordinates(0.5, 0.5)),
            geometry=AlwaysValidGeometryPort(),
            routing=FixedRoutingPort(distance_km=5.0, duration_minutes=10.0),
            demand_provider=PerBusinessDemandPort({"biz-A": 0, "biz-B": 0}),
            clock=FixedClock(_MONDAY_NOON),
            price_calculator=DeliveryPriceCalculator(),
        )

        dest = AddressInput(street="X", street_number="1", city="Y", province="Z")
        result_a = uc.execute(CalculateDeliveryQuoteCommand(business_config_id="biz-A", destination_address=dest))
        result_b = uc.execute(CalculateDeliveryQuoteCommand(business_config_id="biz-B", destination_address=dest))

        assert result_a.available
        assert result_b.available
        assert result_a.shipping_cost != result_b.shipping_cost
        # biz-A: 5km * 10 = 50; biz-B: 5km * 20 = 100
        assert result_a.shipping_cost == Decimal("50.00")
        assert result_b.shipping_cost == Decimal("100.00")

    def test_demand_is_isolated_per_restaurant(self):
        """High demand for biz-A should NOT affect biz-B's quote."""
        repo = InMemoryDeliveryConfigurationRepository()
        repo.save(_make_config("biz-A", price_per_km=Decimal("0.00"), base=Decimal("100.00")))
        repo.save(_make_config("biz-B", price_per_km=Decimal("0.00"), base=Decimal("100.00")))

        uc = CalculateDeliveryQuoteUseCase(
            delivery_config_repo=repo,
            geocoding=FixedGeocodingPort(Coordinates(0.5, 0.5)),
            geometry=AlwaysValidGeometryPort(),
            routing=FixedRoutingPort(distance_km=0.0, duration_minutes=0.0),
            demand_provider=PerBusinessDemandPort({
                "biz-A": 10,  # VERY_HIGH (2x)
                "biz-B": 0,   # NORMAL
            }),
            clock=FixedClock(_MONDAY_NOON),
            price_calculator=DeliveryPriceCalculator(),
        )

        dest = AddressInput(street="X", street_number="1", city="Y", province="Z")
        result_a = uc.execute(CalculateDeliveryQuoteCommand(business_config_id="biz-A", destination_address=dest))
        result_b = uc.execute(CalculateDeliveryQuoteCommand(business_config_id="biz-B", destination_address=dest))

        assert result_a.demand_level == "VERY_HIGH"
        assert result_b.demand_level == "NORMAL"
        assert result_a.shipping_cost == Decimal("200.00")
        assert result_b.shipping_cost == Decimal("100.00")
