"""Django app config for the config_coupon module."""

from __future__ import annotations

from django.apps import AppConfig


class ConfigCouponConfig(AppConfig):
    """Registers the config_coupon bounded context in Django."""

    name = "modules.config_coupon"
    label = "config_coupon"
    verbose_name = "Coupons & configuration"