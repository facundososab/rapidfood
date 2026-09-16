"""Django app config for the delivery module."""

from __future__ import annotations

from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    """Registers the delivery bounded context in Django."""

    name = "modules.delivery"
    label = "delivery"
    verbose_name = "Delivery"
