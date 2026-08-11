"""URL routing — Rapidfood.

Route layout: ``/health`` plus per-app inbound adapters added by later changes.
"""

from django.urls import path

from api.config import views

urlpatterns = [
    path("health/", views.health, name="health"),
]
