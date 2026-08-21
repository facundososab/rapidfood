"""Delivery domain errors.

All domain errors inherit from DeliveryDomainError so callers can catch
the base class and REST adapters can translate to HTTP codes consistently.
"""

from __future__ import annotations


class DeliveryDomainError(Exception):
    """Base class for all delivery domain errors."""


class BusinessConfigurationNotFoundError(DeliveryDomainError):
    """Raised when the requested business configuration does not exist."""


class DeliveryConfigurationNotFoundError(DeliveryDomainError):
    """Raised when delivery has not been configured for this restaurant yet."""


class InvalidDeliveryZoneError(DeliveryDomainError):
    """Raised when a delivery zone polygon is invalid or malformed."""


class DeliveryZoneNotConfiguredError(DeliveryDomainError):
    """Raised when a restaurant has no delivery zone set."""


class InvalidDeliveryPricingConfigurationError(DeliveryDomainError):
    """Raised when pricing configuration values violate business invariants."""


class IncompleteWeekdayPricingRulesError(DeliveryDomainError):
    """Raised when not all 7 weekday pricing rules are provided."""


class DeliveryOriginNotConfiguredError(DeliveryDomainError):
    """Raised when an origin address has not been selected."""


class DeliveryOriginDoesNotBelongToBusinessError(DeliveryDomainError):
    """Raised when the chosen origin address belongs to a different restaurant."""


class AddressCouldNotBeGeocodedError(DeliveryDomainError):
    """Raised when the geocoding provider cannot resolve the given address."""


class GeocodingProviderError(DeliveryDomainError):
    """Raised when the geocoding provider fails for a technical reason."""


class RoutingProviderError(DeliveryDomainError):
    """Raised when the routing provider fails for a technical reason."""
