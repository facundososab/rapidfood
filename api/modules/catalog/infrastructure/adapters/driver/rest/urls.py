from django.urls import path

from .views import (
    CategoryListCreateView,
    PriceListCreateView,
    ProductDetailView,
    ProductListCreateView,
    SetDiscountView,
    SetProductStateView,
)


from .views_variants import (
    ProductVariantListView,
    ProductVariantDetailView,
    VariantPriceView,
    IngredientListView,
    IngredientDetailView,
    VariantIngredientsView,
    ModifierGroupListView,
    ModifierGroupDetailView,
    ModifierOptionListView,
    ModifierOptionDetailView,
)

urlpatterns = [
    path('products/<uuid:product_id>/variants/', ProductVariantListView.as_view(), name='product-variant-list'),
    path('variants/<uuid:variant_id>/', ProductVariantDetailView.as_view(), name='variant-detail'),
    path('variants/<uuid:variant_id>/prices/', VariantPriceView.as_view(), name='variant-price'),
    path('variants/<uuid:variant_id>/ingredients/', VariantIngredientsView.as_view(), name='variant-ingredients'),
    path('ingredients/', IngredientListView.as_view(), name='ingredient-list'),
    path('ingredients/<uuid:ingredient_id>/', IngredientDetailView.as_view(), name='ingredient-detail'),
    path('products/<uuid:product_id>/modifier-groups/', ModifierGroupListView.as_view(), name='modifier-group-list'),
    path('modifier-groups/<uuid:group_id>/', ModifierGroupDetailView.as_view(), name='modifier-group-detail'),
    path('modifier-groups/<uuid:group_id>/options/', ModifierOptionListView.as_view(), name='modifier-option-list'),
    path('modifier-options/<uuid:option_id>/', ModifierOptionDetailView.as_view(), name='modifier-option-detail'),

    path("products/", ProductListCreateView.as_view(), name="catalog-products"),
    path(
        "products/<str:product_id>/",
        ProductDetailView.as_view(),
        name="catalog-product-detail",
    ),
    path(
        "products/<str:product_id>/state/",
        SetProductStateView.as_view(),
        name="catalog-product-state",
    ),
    path(
        "products/<str:product_id>/prices/",
        PriceListCreateView.as_view(),
        name="catalog-product-prices",
    ),
    path("categories/", CategoryListCreateView.as_view(), name="catalog-categories"),
    path("discounts/", SetDiscountView.as_view(), name="catalog-discounts"),
]