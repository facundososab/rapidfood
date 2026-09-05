from django.urls import path

from .views import (
    ClientAddressDetailView,
    ClientAddressListView,
    ClientAddressSetDefaultView,
    ClientDetailView,
    ClientListView,
)

urlpatterns = [
    path("", ClientListView.as_view(), name="client-list-create"),
    path("<str:client_id>/", ClientDetailView.as_view(), name="client-detail"),
    path(
        "<str:client_id>/addresses/",
        ClientAddressListView.as_view(),
        name="client-address-list-create",
    ),
    path(
        "<str:client_id>/addresses/<str:address_id>/",
        ClientAddressDetailView.as_view(),
        name="client-address-detail",
    ),
    path(
        "<str:client_id>/addresses/<str:address_id>/set-default/",
        ClientAddressSetDefaultView.as_view(),
        name="client-address-set-default",
    ),
]
