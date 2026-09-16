from modules.catalog.domain.models.product_variant import ProductVariant


def test_product_variant_defaults_available():
    variant = ProductVariant(id="v-1", product_id="p-1", name="Default")
    assert variant.available is True


def test_product_variant_mark_unavailable():
    variant = ProductVariant(id="v-1", product_id="p-1", name="Default", available=True)
    variant.mark_unavailable()
    assert variant.available is False


def test_product_variant_mark_available():
    variant = ProductVariant(id="v-1", product_id="p-1", name="Default", available=False)
    variant.mark_available()
    assert variant.available is True
