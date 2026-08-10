from django.urls import path
from .views import (
    ClientListCreateView,
    ClientDetailView,
    ClientAddressListView,
    ClientAddressDetailView,
    ClientAddressSetDefaultView,
)

urlpatterns = [
    path("clients/", ClientListCreateView.as_view(), name="client-list-create"),
    path("clients/<str:pk>/", ClientDetailView.as_view(), name="client-detail"),
    path(
        "clients/<str:pk>/addresses/",
        ClientAddressListView.as_view(),
        name="client-address-list-create",
    ),
    path(
        "clients/<str:pk>/addresses/<str:address_id>/",
        ClientAddressDetailView.as_view(),
        name="client-address-detail",
    ),
    path(
        "clients/<str:pk>/addresses/<str:address_id>/set-default/",
        ClientAddressSetDefaultView.as_view(),
        name="client-address-set-default",
    ),
]
