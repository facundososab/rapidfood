from rest_framework import serializers

class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255)
    category_id = serializers.CharField()

class SetProductStateSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=["available", "unavailable"])


class AddPriceSerializer(serializers.Serializer):
    since_date = serializers.DateField(required=False, default=None)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateCategorySerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255)


class UpdateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=255, required=False)
    category_id = serializers.CharField(required=False)
    available = serializers.BooleanField(required=False)


class SetDiscountSerializer(serializers.Serializer):
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    product_id = serializers.CharField(required=False, allow_null=True)