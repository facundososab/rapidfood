"""DRF serializers for the coupon REST adapter.

Serializers validate TRANSPORT format only (types, required fields). Business
rules stay in the domain/Coupon entity — never duplicated here.
"""

from __future__ import annotations

from rest_framework import serializers


class CreateCouponSerializer(serializers.Serializer):
    coupon_code = serializers.CharField()
    coupon_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    available_uses = serializers.IntegerField(min_value=0)
    min_order_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    date_of_expiration = serializers.DateTimeField(
        required=False, allow_null=True
    )
    is_active = serializers.BooleanField(required=False, default=True)


class ToggleCouponStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
