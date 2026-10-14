from rest_framework import serializers

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


class CreateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255, allow_blank=True, required=False)
    image_url = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    category_id = serializers.CharField()

class SetProductStateSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=["available", "unavailable"])


class AddPriceSerializer(serializers.Serializer):
    since_date = serializers.DateField(required=False, default=None)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateCategorySerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255, allow_blank=True, required=False)


class UpdateProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=255, required=False)
    image_url = serializers.CharField(max_length=2000, required=False, allow_blank=True, allow_null=True)
    category_id = serializers.CharField(required=False)
    available = serializers.BooleanField(required=False)


class SetDiscountSerializer(serializers.Serializer):
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    product_id = serializers.CharField(required=False, allow_null=True)


class ProductImageUploadSerializer(serializers.Serializer):
    image = serializers.FileField()

    def validate_image(self, value):
        content_type = getattr(value, "content_type", "")
        if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise serializers.ValidationError(
                "Formato de imagen no permitido. Usar JPEG, PNG, WEBP o GIF."
            )
        if value.size > MAX_IMAGE_SIZE_BYTES:
            raise serializers.ValidationError(
                "La imagen supera el tamano maximo de 5 MB."
            )
        return value
