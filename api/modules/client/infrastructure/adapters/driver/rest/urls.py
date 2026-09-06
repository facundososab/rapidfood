from django.urls import path

from .views import (
    AddAddressView,
    CreateClientView,
    DeleteClientView,
    GetClientView,
    ListClientsView,
    RemoveAddressView,
    SetDefaultAddressView,
    UpdateAddressView,
    UpdateClientView,
)

urlpatterns = [
    path("", ListClientsView.as_view(), name="client-list"),
    path("create/", CreateClientView.as_view(), name="client-create"),
    path("<str:client_id>/", GetClientView.as_view(), name="client-detail"),
    path("<str:client_id>/update/", UpdateClientView.as_view(), name="client-update"),
    path("<str:client_id>/delete/", DeleteClientView.as_view(), name="client-delete"),
    path("<str:client_id>/addresses/", AddAddressView.as_view(), name="client-address-create"),
    path(
        "<str:client_id>/addresses/<str:address_id>/update/",
        UpdateAddressView.as_view(),
        name="client-address-update",
    ),
    path(
        "<str:client_id>/addresses/<str:address_id>/remove/",
        RemoveAddressView.as_view(),
        name="client-address-remove",
    ),
    path(
        "<str:client_id>/addresses/<str:address_id>/set-default/",
        SetDefaultAddressView.as_view(),
        name="client-address-set-default",
    ),
]
