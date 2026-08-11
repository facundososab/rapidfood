from django.urls import path

from .views import (
    CreateCategoryView,
    PriceListCreateView,
    ProductListCreateView,
    SetDiscountView,
    SetProductStateView,
)

urlpatterns = [
    path("products/", ProductListCreateView.as_view(), name="catalog-products"),
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
    path("categories/", CreateCategoryView.as_view(), name="catalog-categories"),
    path("discounts/", SetDiscountView.as_view(), name="catalog-discounts"),
]