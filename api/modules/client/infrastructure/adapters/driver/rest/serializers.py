from rest_framework import serializers


class CreateClientRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=30)


class UpdateClientRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=30)


class AddressRequestSerializer(serializers.Serializer):
    street = serializers.CharField(max_length=255)
    street_number = serializers.CharField(max_length=50)
    floor = serializers.CharField(max_length=20, required=False, allow_null=True)
    apartment = serializers.CharField(max_length=20, required=False, allow_null=True)
    city = serializers.CharField(max_length=100)
    province = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20, required=False, allow_null=True)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    delivery_instructions = serializers.CharField(required=False, allow_null=True)
    label = serializers.CharField(max_length=50, required=False, allow_null=True)
    is_default = serializers.BooleanField(default=False)
