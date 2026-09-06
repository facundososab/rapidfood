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
    OrderListView,
    AllOrdersView,
    OrderDetailView,
    UpdateOrderStatusView,
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('all/', AllOrdersView.as_view(), name='order-all'),
    path('draft/', StartDraftOrderView.as_view(), name='start-draft-order'),
    path('<uuid:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<uuid:order_id>/status/', UpdateOrderStatusView.as_view(), name='order-status'),
    path('<uuid:order_id>/lines/', AddLineView.as_view(), name='add-line'),
    path('<uuid:order_id>/lines/<uuid:line_id>/', UpdateLineQuantityView.as_view(), name='update-line-quantity'),
    path('<uuid:order_id>/lines/<uuid:line_id>/remove/', RemoveLineView.as_view(), name='remove-line'),
    path('<uuid:order_id>/delivery/', SetDeliveryDetailsView.as_view(), name='set-delivery-details'),
    path('<uuid:order_id>/coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
    path('<uuid:order_id>/confirm/', ConfirmOrderView.as_view(), name='confirm-order'),
    path('<uuid:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('<uuid:order_id>/advance/', AdvanceStateView.as_view(), name='advance-state'),
]