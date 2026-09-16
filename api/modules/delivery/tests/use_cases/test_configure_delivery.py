"""Use case tests for ConfigureDeliveryUseCase."""

from __future__ import annotations

from decimal import Decimal
from typing import Dict

import pytest

from modules.delivery.application.ports.driver.configure_delivery_ports import (
    ConfigureDeliveryCommand,
    CoordinateInput,
    DeliveryZoneInput,
    WeekdayMultiplierInput,
)
from modules.delivery.application.use_cases.configure_delivery_use_case import (
    ConfigureDeliveryUseCase,
)
from modules.delivery.domain.errors.delivery_errors import (
    DeliveryOriginDoesNotBelongToBusinessError,
    DeliveryOriginNotConfiguredError,
    InvalidDeliveryZoneError,
    IncompleteWeekdayPricingRulesError,
)
from modules.delivery.domain.models.week_day import WeekDay
from modules.delivery.tests.use_cases.fakes import (
    AlwaysValidGeometryPort,
    FakeBusinessAddressQuery,
    InMemoryDeliveryConfigurationRepository,
    RejectingGeometryPort,
)

_BIZ_ID = "biz-001"
_ADDR_ID = "addr-001"
_OTHER_BIZ_ID = "biz-002"


def _all_weekday_inputs(value: str = "1.00") -> list:
    return [
        WeekdayMultiplierInput(week_day=day.value, multiplier=Decimal(value))
        for day in WeekDay
    ]


def _square_zone() -> DeliveryZoneInput:
    return DeliveryZoneInput(
        exterior_ring=[
            CoordinateInput(longitude=0.0, latitude=0.0),
            CoordinateInput(longitude=1.0, latitude=0.0),
            CoordinateInput(longitude=1.0, latitude=1.0),
            CoordinateInput(longitude=0.0, latitude=0.0),
        ]
    )


def _command(**overrides) -> ConfigureDeliveryCommand:
    defaults = dict(
        business_config_id=_BIZ_ID,
        base_shipping_cost=Decimal("50.00"),
        origin_address_id=_ADDR_ID,
        delivery_zone=_square_zone(),
        price_per_km=Decimal("10.00"),
        high_demand_threshold=5,
        very_high_demand_threshold=10,
        high_demand_multiplier=Decimal("1.50"),
        very_high_demand_multiplier=Decimal("2.00"),
        weekday_multipliers=_all_weekday_inputs(),
    )
    defaults.update(overrides)
    return ConfigureDeliveryCommand(**defaults)


def _make_uc(address_query=None, geometry=None, repo=None):
    if address_query is None:
        address_query = FakeBusinessAddressQuery()
        address_query.add(_ADDR_ID, _BIZ_ID)
    return ConfigureDeliveryUseCase(
        delivery_config_repo=repo or InMemoryDeliveryConfigurationRepository(),
        address_query=address_query,
        geometry=geometry or AlwaysValidGeometryPort(),
    )


class TestHappyPath:
    def test_configure_saves_configuration(self):
        repo = InMemoryDeliveryConfigurationRepository()
        uc = _make_uc(repo=repo)
        result = uc.execute(_command())
        assert result.business_config_id == _BIZ_ID
        saved = repo.get_by_business_config_id(_BIZ_ID)
        assert saved is not None
        assert saved.delivery_zone is not None
        assert saved.pricing_config is not None

    def test_can_update_configuration(self):
        repo = InMemoryDeliveryConfigurationRepository()
        uc = _make_uc(repo=repo)
        uc.execute(_command())
        # Update with a different price_per_km
        uc.execute(_command(price_per_km=Decimal("20.00")))
        saved = repo.get_by_business_config_id(_BIZ_ID)
        assert saved.pricing_config.price_per_km == Decimal("20.00")


class TestOriginAddressValidation:
    def test_raises_when_address_does_not_exist(self):
        address_query = FakeBusinessAddressQuery()  # empty
        uc = _make_uc(address_query=address_query)
        with pytest.raises(DeliveryOriginNotConfiguredError):
            uc.execute(_command())

    def test_raises_when_address_belongs_to_different_business(self):
        address_query = FakeBusinessAddressQuery()
        address_query.add(_ADDR_ID, _OTHER_BIZ_ID)  # belongs to other business
        uc = _make_uc(address_query=address_query)
        with pytest.raises(DeliveryOriginDoesNotBelongToBusinessError):
            uc.execute(_command())


class TestZoneValidation:
    def test_raises_when_polygon_is_invalid(self):
        uc = _make_uc(geometry=RejectingGeometryPort())
        with pytest.raises(InvalidDeliveryZoneError):
            uc.execute(_command())


class TestPricingConfigValidation:
    def test_raises_when_missing_weekday_rules(self):
        partial_days = _all_weekday_inputs()[:6]  # only 6 of 7
        uc = _make_uc()
        with pytest.raises(IncompleteWeekdayPricingRulesError):
            uc.execute(_command(weekday_multipliers=partial_days))
