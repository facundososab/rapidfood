"""URLs of the Mercado Pago linkage module.

The paths already carry the ``mercadopago/`` segment, so the wiring root must
include this module at the API root::

    path("api/", include("modules.mercadopago.infrastructure.adapters.driver.rest.urls"))

which resolves to ``/api/mercadopago/authorize/``, ``/api/mercadopago/callback/``,
``/api/mercadopago/status/`` and ``/api/mercadopago/unlink/``.
"""

from django.urls import path

from .views import (
    MercadoPagoAuthorizeView,
    MercadoPagoCallbackView,
    MercadoPagoStatusView,
    MercadoPagoUnlinkView,
)

urlpatterns = [
    path("mercadopago/authorize/", MercadoPagoAuthorizeView.as_view(), name="mercadopago-authorize"),
    path("mercadopago/callback/", MercadoPagoCallbackView.as_view(), name="mercadopago-callback"),
    path("mercadopago/status/", MercadoPagoStatusView.as_view(), name="mercadopago-status"),
    path("mercadopago/unlink/", MercadoPagoUnlinkView.as_view(), name="mercadopago-unlink"),
]
