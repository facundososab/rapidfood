from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from composition.container import get_app_container
from modules.order.application.ports.driver.start_draft_order_ports import StartDraftOrderCommand
from modules.order.application.ports.driver.add_line_port import AddLineCommand
from modules.order.application.ports.driver.update_line_quantity_port import UpdateLineQuantityCommand
from modules.order.application.ports.driver.remove_line_port import RemoveLineCommand
from modules.order.application.ports.driver.configure_order_ports import SetDeliveryDetailsCommand
from modules.order.application.ports.driver.confirm_order_ports import ConfirmOrderCommand
from modules.order.application.ports.driver.apply_coupon_ports import ApplyCouponCommand
from modules.order.application.ports.driver.cancel_order_ports import CancelOrderCommand
from modules.order.application.ports.driver.advance_state_ports import AdvanceStateCommand
from modules.order.application.ports.driver.list_orders_ports import ListOrdersQuery
from modules.order.application.ports.driver.update_order_status_ports import (
    UpdateOrderStatusCommand,
)
from modules.order.domain.errors.order_errors import OrderDomainError
from modules.order.domain.models.order import Order
from .serializers import (
    StartDraftOrderSerializer, AddLineSerializer, UpdateLineQuantitySerializer,
    SetDeliveryDetailsSerializer, ConfirmOrderSerializer, ApplyCouponSerializer,
    CancelOrderSerializer, AdvanceStateSerializer, UpdateOrderStatusSerializer
)


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "status": order.status.value,
        "origin": order.origin.value,
        "subtotal": order.subtotal,
        "discount": order.discount,
        "client_id": order.client_id,
        "address_id": order.address_id,
        "conversation_id": order.conversation_id,
        "estimated_time": order.estimated_time,
        "delivery_type": order.delivery_type.value if order.delivery_type else None,
        "payment_type": order.payment_type.value if order.payment_type else None,
        "shipping_cost": order.shipping_cost,
        "total_amount": order.total_amount,
        "applied_coupon_id": order.applied_coupon_id,
        "confirmed_at": order.confirmed_at,
        "created_at": order.created_at,
        "lines": [
            {
                "id": line.id,
                "order_id": line.order_id,
                "product_id": line.product_id,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "subtotal": line.subtotal,
                "discount_id": line.discount_id,
            }
            for line in order.lines
        ],
    }


class OrderListView(APIView):
    def get(self, request):
        query = ListOrdersQuery(
            status=request.query_params.get("status"),
            delivery_type=request.query_params.get("delivery_type"),
            payment_type=request.query_params.get("payment_type"),
            search=request.query_params.get("search"),
            date_from=_parse_dt(request.query_params.get("date_from")),
            date_to=_parse_dt(request.query_params.get("date_to")),
        )
        container = get_app_container()
        try:
            orders = container.list_orders_use_case.execute(query)
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response([_order_to_dict(order) for order in orders])


class AllOrdersView(APIView):
    def get(self, request):
        container = get_app_container()
        orders = container.list_orders_use_case.execute(ListOrdersQuery())
        return Response([_order_to_dict(order) for order in orders])


class OrderDetailView(APIView):
    def get(self, request, order_id):
        container = get_app_container()
        order = container.get_order_use_case.execute(str(order_id))
        if order is None:
            return Response(
                {"detail": "La orden no existe"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(_order_to_dict(order))


class UpdateOrderStatusView(APIView):
    def patch(self, request, order_id):
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = UpdateOrderStatusCommand(
            order_id=str(order_id), **serializer.validated_data
        )
        container = get_app_container()
        try:
            response = container.update_order_status.execute(command)
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response({"order_id": response.order_id, "status": response.status})


class StartDraftOrderView(APIView):
    def post(self, request):
        serializer = StartDraftOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = StartDraftOrderCommand(**serializer.validated_data)
        
        container = get_app_container()
        try:
            response = container.start_draft_order_use_case.execute(command)
            return Response(
                {"order_id": response.order_id, "status": response.status},
                status=status.HTTP_201_CREATED
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddLineView(APIView):
    def post(self, request, order_id):
        serializer = AddLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # We ensure product_id is cast to string correctly if needed, or rely on UUID
        validated = serializer.validated_data.copy()
        validated['product_id'] = str(validated['product_id'])
        
        command = AddLineCommand(
            order_id=str(order_id),
            **validated
        )
        
        container = get_app_container()
        try:
            response = container.add_line_use_case.add_line(command)
            return Response(
                {
                    "order_id": response.order_id,
                    "total_amount": response.total_amount,
                    "line_count": response.line_count
                },
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UpdateLineQuantityView(APIView):
    def patch(self, request, order_id, product_id):
        serializer = UpdateLineQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = UpdateLineQuantityCommand(
            order_id=str(order_id),
            product_id=str(product_id),
            **serializer.validated_data
        )
        
        container = get_app_container()
        try:
            response = container.update_line_quantity_use_case.update_line_quantity(command)
            return Response(
                {
                    "order_id": response.order_id,
                    "total_amount": response.total_amount,
                    "line_count": response.line_count
                },
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SetDeliveryDetailsView(APIView):
    def patch(self, request, order_id):
        serializer = SetDeliveryDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = SetDeliveryDetailsCommand(
            order_id=str(order_id),
            **serializer.validated_data
        )
        
        container = get_app_container()
        try:
            response = container.configure_order_use_case.set_delivery_details(command)
            return Response(
                {
                    "order_id": response.order_id,
                    "shipping_cost": response.shipping_cost,
                    "total_amount": response.total_amount
                },
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConfirmOrderView(APIView):
    def post(self, request, order_id):
        serializer = ConfirmOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = ConfirmOrderCommand(
            order_id=str(order_id)
        )
        
        container = get_app_container()
        try:
            response = container.confirm_order_use_case.execute(command)
            return Response(
                {
                    "order_id": response.order_id,
                    "status": response.status,
                    "confirmed_at": response.confirmed_at
                },
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            # For more granular REST practices, one might return 409 for State errors, 422 for Validation etc.
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RemoveLineView(APIView):
    def delete(self, request, order_id, product_id):
        command = RemoveLineCommand(
            order_id=str(order_id),
            product_id=str(product_id)
        )
        container = get_app_container()
        try:
            response = container.remove_line_use_case.execute(command)
            return Response(
                {
                    "order_id": response.order_id,
                    "total_amount": response.total_amount,
                    "line_count": response.line_count
                },
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ApplyCouponView(APIView):
    def post(self, request, order_id):
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = ApplyCouponCommand(
            order_id=str(order_id),
            **serializer.validated_data
        )
        container = get_app_container()
        try:
            response = container.apply_coupon_use_case.apply(command)
            return Response(
                {
                    "order_id": response.order_id,
                    "coupon_code": response.coupon_code,
                    "discount_applied": response.discount_applied,
                    "total_amount": response.total_amount
                },
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(APIView):
    def post(self, request, order_id):
        serializer = CancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = CancelOrderCommand(
            order_id=str(order_id),
            **serializer.validated_data
        )
        container = get_app_container()
        try:
            response = container.cancel_order_use_case.execute(command)
            return Response(
                {"order_id": response.order_id, "status": response.status},
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)


class AdvanceStateView(APIView):
    def post(self, request, order_id):
        serializer = AdvanceStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = AdvanceStateCommand(
            order_id=str(order_id),
            **serializer.validated_data
        )
        container = get_app_container()
        try:
            response = container.advance_state_use_case.execute(command)
            return Response(
                {
                    "order_id": response.order_id,
                    "previous_state": response.previous_state,
                    "new_state": response.new_state
                },
                status=status.HTTP_200_OK
            )
        except OrderDomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
