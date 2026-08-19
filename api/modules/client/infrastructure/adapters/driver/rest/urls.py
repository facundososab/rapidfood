from django.urls import path

from .views import ClientDetailView, ClientListView

urlpatterns = [
    path("", ClientListView.as_view(), name="client-list"),
    path("<str:client_id>/", ClientDetailView.as_view(), name="client-detail"),
]