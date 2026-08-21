"""URL routing for the config_coupon REST inbound adapter.

Views receive their use cases from the module's container at wiring time.
These routes must be included from the project root urlconf.
"""

from __future__ import annotations

from django.urls import path

from modules.config_coupon.configuration import get_coupon_container
from modules.config_coupon.infrastructure.adapters.driver.rest import views

_container = get_coupon_container()

# Inject concrete use cases from the composition root into the views.
_create_coupon = views.CreateCouponView.as_view(
    create_coupon=_container.create_coupon
)
_list_coupons = views.ListCouponsView.as_view(list_coupons=_container.list_coupons)
_get_coupon_by_code = views.GetCouponByCodeView.as_view(
    get_coupon_by_code=_container.get_coupon_by_code
)
_toggle_status = views.ToggleCouponStatusView.as_view(
    toggle_coupon_status=_container.toggle_coupon_status
)
_validate_coupon = views.ValidateCouponView.as_view(
    validate_coupon=_container.validate_coupon
)
_consume_coupon = views.ConsumeCouponView.as_view(
    consume_coupon=_container.consume_coupon
)

urlpatterns = [
    path("coupons/", _create_coupon, name="coupon-create"),
    path("coupons/list/", _list_coupons, name="coupon-list"),
    path("coupons/by-code/<str:coupon_code>/", _get_coupon_by_code, name="coupon-by-code"),
    path(
        "coupons/<str:coupon_id>/status/",
        _toggle_status,
        name="coupon-toggle-status",
    ),
    path("coupons/validate/", _validate_coupon, name="coupon-validate"),
    path("coupons/consume/<str:coupon_code>/", _consume_coupon, name="coupon-consume"),
]