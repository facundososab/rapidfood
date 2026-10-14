from django.core.files.uploadedfile import SimpleUploadedFile

from modules.catalog.infrastructure.adapters.driver.rest.serializers import (
    MAX_IMAGE_SIZE_BYTES,
    ProductImageUploadSerializer,
)


def test_accepts_allowed_image_type():
    upload = SimpleUploadedFile("p.jpg", b"data", content_type="image/jpeg")
    serializer = ProductImageUploadSerializer(data={"image": upload})

    assert serializer.is_valid(), serializer.errors


def test_rejects_disallowed_content_type():
    upload = SimpleUploadedFile("p.txt", b"data", content_type="text/plain")
    serializer = ProductImageUploadSerializer(data={"image": upload})

    assert not serializer.is_valid()
    assert "image" in serializer.errors


def test_rejects_oversized_image():
    upload = SimpleUploadedFile(
        "p.jpg", b"x" * (MAX_IMAGE_SIZE_BYTES + 1), content_type="image/jpeg"
    )
    serializer = ProductImageUploadSerializer(data={"image": upload})

    assert not serializer.is_valid()
    assert "image" in serializer.errors
