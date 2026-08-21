"""DRF serializers for the delivery REST inbound adapter."""

from __future__ import annotations

from rest_framework import serializers


class CoordinateSerializer(serializers.Serializer):
    """A single geographic point in [longitude, latitude] order (GeoJSON standard)."""

    longitude = serializers.FloatField()
    latitude = serializers.FloatField()


class DeliveryZoneInputSerializer(serializers.Serializer):
    """GeoJSON Polygon input for the delivery zone."""

    exterior_ring = CoordinateSerializer(many=True)
    holes = CoordinateSerializer(many=True, required=False, default=list)

    def validate_exterior_ring(self, value):  # type: ignore[override]
        if len(value) < 4:
            raise serializers.ValidationError(
                "exterior_ring must have at least 4 coordinate pairs "
                "(3 unique + closing point)."
            )
        return value


class WeekdayMultiplierSerializer(serializers.Serializer):
    VALID_DAYS = {
        "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
        "FRIDAY", "SATURDAY", "SUNDAY",
    }

    week_day = serializers.CharField()
    multiplier = serializers.DecimalField(max_digits=5, decimal_places=2)

    def validate_week_day(self, value):  # type: ignore[override]
        if value.upper() not in self.VALID_DAYS:
            raise serializers.ValidationError(
                f"'{value}' is not a valid weekday. "
                f"Valid values: {', '.join(sorted(self.VALID_DAYS))}"
            )
        return value.upper()

    def validate_multiplier(self, value):  # type: ignore[override]
        if value <= 0:
            raise serializers.ValidationError("Multiplier must be > 0.")
        return value


class ConfigureDeliverySerializer(serializers.Serializer):
    """Validates the full delivery configuration input."""

    base_shipping_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0
    )
    origin_address_id = serializers.UUIDField()
    delivery_zone = DeliveryZoneInputSerializer()
    price_per_km = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0
    )
    high_demand_threshold = serializers.IntegerField(min_value=0)
    very_high_demand_threshold = serializers.IntegerField(min_value=1)
    high_demand_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0
    )
    very_high_demand_multiplier = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0
    )
    weekday_multipliers = WeekdayMultiplierSerializer(many=True)

    def validate(self, data):  # type: ignore[override]
        if data.get("very_high_demand_threshold", 0) <= data.get(
            "high_demand_threshold", 0
        ):
            raise serializers.ValidationError(
                "very_high_demand_threshold must be greater than high_demand_threshold."
            )
        if len(data.get("weekday_multipliers", [])) != 7:
            raise serializers.ValidationError(
                "weekday_multipliers must contain exactly 7 entries (one per day)."
            )
        days = [e["week_day"] for e in data.get("weekday_multipliers", [])]
        if len(set(days)) != 7:
            raise serializers.ValidationError(
                "weekday_multipliers must contain exactly one entry per weekday."
            )
        return data


class AddressInputSerializer(serializers.Serializer):
    """Destination address for a delivery quote."""

    street = serializers.CharField(max_length=255)
    street_number = serializers.CharField(max_length=50)
    city = serializers.CharField(max_length=100)
    province = serializers.CharField(max_length=100)
    floor = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True, default=None)
    apartment = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True, default=None)
    postal_code = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True, default=None)


class CalculateDeliveryQuoteSerializer(serializers.Serializer):
    """Validates the delivery quote request body."""

    destination_address = AddressInputSerializer()
