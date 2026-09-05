from rest_framework import serializers

class StartDraftOrderSerializer(serializers.Serializer):
    client_id = serializers.UUIDField(required=False, allow_null=True)
    business_config_id = serializers.CharField(required=False, allow_null=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    origin = serializers.ChoiceField(
        choices=["IN_PLACE", "AGENT"], required=False, allow_null=True
    )

class AddLineSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

class UpdateLineQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True, min_value=1)

class SetDeliveryDetailsSerializer(serializers.Serializer):
    delivery_type = serializers.CharField(max_length=50, required=True)
    address_id = serializers.UUIDField(required=False, allow_null=True)

class ConfirmOrderSerializer(serializers.Serializer):
    # No additional fields needed since the order ID comes from the URL
    pass


class ApplyCouponSerializer(serializers.Serializer):
    coupon_code = serializers.CharField()


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, default="", allow_blank=True)


class AdvanceStateSerializer(serializers.Serializer):
    target_state = serializers.CharField()


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
