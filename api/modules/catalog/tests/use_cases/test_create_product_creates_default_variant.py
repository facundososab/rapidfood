from unittest.mock import Mock, call
from modules.catalog.application.ports.driver.create_product_ports import CreateProductCommand


def test_create_product_also_creates_default_variant():
    """
    When a new product is created, a 'Default' variant must be auto-created.
    """
    # We'll verify by checking the variant_repo.save was called
    from modules.catalog.application.use_cases.create_product_use_case import CreateProductUseCase

    mock_product_repo = Mock()
    mock_category_repo = Mock()
    mock_id_generator = Mock()
    mock_id_generator.generate.side_effect = ["product-uuid", "variant-uuid"]
    mock_variant_repo = Mock()

    # Stub category
    from modules.catalog.domain.models.category import Category
    mock_category_repo.find_by_id.return_value = Category(id="cat-1", description="Burgers")

    uc = CreateProductUseCase(
        product_repo=mock_product_repo,
        category_repo=mock_category_repo,
        id_generator=mock_id_generator,
        variant_repo=mock_variant_repo,
    )

    uc.execute(CreateProductCommand(name="Stacker", description="Desc", category_id="cat-1"))

    # product saved
    mock_product_repo.save.assert_called_once()
    # default variant saved
    mock_variant_repo.save.assert_called_once()
    saved_variant = mock_variant_repo.save.call_args[0][0]
    assert saved_variant.name == "Default"
    assert saved_variant.product_id == "product-uuid"
