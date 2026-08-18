from django.urls import path
from .views import (
    StartDraftOrderView,
    AddLineView,
    UpdateLineQuantityView,
    RemoveLineView,
    SetDeliveryDetailsView,
    ApplyCouponView,
    ConfirmOrderView,
    CancelOrderView,
    AdvanceStateView,
)

urlpatterns = [
    path('draft/', StartDraftOrderView.as_view(), name='start-draft-order'),
    path('<uuid:order_id>/lines/', AddLineView.as_view(), name='add-line'),
    path('<uuid:order_id>/lines/<uuid:product_id>/', UpdateLineQuantityView.as_view(), name='update-line-quantity'),
    path('<uuid:order_id>/lines/<uuid:product_id>/remove/', RemoveLineView.as_view(), name='remove-line'),
    path('<uuid:order_id>/delivery/', SetDeliveryDetailsView.as_view(), name='set-delivery-details'),
    path('<uuid:order_id>/coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('<uuid:order_id>/confirm/', ConfirmOrderView.as_view(), name='confirm-order'),
    path('<uuid:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('<uuid:order_id>/advance/', AdvanceStateView.as_view(), name='advance-state'),
]

