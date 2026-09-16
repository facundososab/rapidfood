"""DeliveryPriceCalculator — pure domain service.

Calculates the final shipping cost given route metrics, pricing config,
weekday multiplier, and demand multiplier. No external dependencies.

Formula:
    distance_charge = distance_km * price_per_km
    subtotal        = base_shipping_cost + distance_charge
    shipping_cost   = subtotal * weekday_multiplier * demand_multiplier

Result is rounded to 0.01 using ROUND_HALF_UP for consistency with the
rest of Rapidfood monetary calculations.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


class DeliveryPriceCalculator:
    """Stateless domain service for computing delivery cost."""

    _CENT = Decimal("0.01")

    def calculate(
        self,
        base_shipping_cost: Decimal,
        distance_km: float,
        price_per_km: Decimal,
        weekday_multiplier: Decimal,
        demand_multiplier: Decimal,
    ) -> Decimal:
        """Return the final shipping cost, rounded to the nearest cent.

        Args:
            base_shipping_cost: Fixed base cost from restaurant config.
            distance_km: Street distance returned by the routing provider.
            price_per_km: Per-km rate from restaurant pricing config.
            weekday_multiplier: Day-of-week rate multiplier (>0).
            demand_multiplier: Demand-level multiplier (1.0 for NORMAL).

        Returns:
            Rounded Decimal shipping cost.
        """
        # Convert distance to Decimal for all monetary math — never use float for money.
        distance_decimal = Decimal(str(distance_km))

        distance_charge = distance_decimal * price_per_km
        subtotal = base_shipping_cost + distance_charge
        raw_cost = subtotal * weekday_multiplier * demand_multiplier

        return raw_cost.quantize(self._CENT, rounding=ROUND_HALF_UP)
