from django.urls import path

from .views import (
    AddressDetailView,
    AddressListView,
    BusinessConfigurationView,
    BusinessHoursView,
)

urlpatterns = [
    path("<str:business_config_id>/", BusinessConfigurationView.as_view(), name="business-config"),
    path("<str:business_config_id>/hours/", BusinessHoursView.as_view(), name="business-hours"),
    path("<str:business_config_id>/addresses/", AddressListView.as_view(), name="business-addresses"),
    path("<str:business_config_id>/addresses/<str:address_id>/", AddressDetailView.as_view(), name="address_detail"),
]
