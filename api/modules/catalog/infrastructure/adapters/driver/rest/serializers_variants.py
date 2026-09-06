from rest_framework import serializers

class CreateVariantSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    initial_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    price_since_date = serializers.DateField(required=False, allow_null=True)

class UpdateVariantSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    available = serializers.BooleanField(required=False)

class SetVariantPriceSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    since_date = serializers.DateField(required=False, allow_null=True)

class CreateIngredientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)

class UpdateIngredientSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)

class IngredientEntrySerializer(serializers.Serializer):
    ingredient_id = serializers.UUIDField()
    removable = serializers.BooleanField(default=True)

class SetVariantIngredientsSerializer(serializers.Serializer):
    entries = IngredientEntrySerializer(many=True)

class CreateModifierGroupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    min_selections = serializers.IntegerField(min_value=0, default=0)
    max_selections = serializers.IntegerField(min_value=1)

class UpdateModifierGroupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    min_selections = serializers.IntegerField(min_value=0, required=False)
    max_selections = serializers.IntegerField(min_value=1, required=False)

class CreateModifierOptionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    price_delta = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

class UpdateModifierOptionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    price_delta = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    available = serializers.BooleanField(required=False)
