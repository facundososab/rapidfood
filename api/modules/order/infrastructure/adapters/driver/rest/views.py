from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from modules.order.configuration.container import get_container
from modules.order.application.ports.driver.start_draft_order_ports import StartDraftOrderCommand
from modules.order.application.ports.driver.add_line_port import AddLineCommand
from modules.order.application.ports.driver.update_line_quantity_port import UpdateLineQuantityCommand
from modules.order.application.ports.driver.remove_line_port import RemoveLineCommand
from modules.order.application.ports.driver.configure_order_ports import SetDeliveryDetailsCommand
from modules.order.application.ports.driver.confirm_order_ports import ConfirmOrderCommand
from modules.order.application.ports.driver.apply_coupon_ports import ApplyCouponCommand
from modules.order.application.ports.driver.cancel_order_ports import CancelOrderCommand
from modules.order.application.ports.driver.advance_state_ports import AdvanceStateCommand
from modules.order.domain.errors.order_errors import OrderDomainError
from .serializers import (
    StartDraftOrderSerializer, AddLineSerializer, UpdateLineQuantitySerializer,
    SetDeliveryDetailsSerializer, ConfirmOrderSerializer, ApplyCouponSerializer,
    CancelOrderSerializer, AdvanceStateSerializer
)


class StartDraftOrderView(APIView):
    def post(self, request):
        serializer = StartDraftOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        command = StartDraftOrderCommand(**serializer.validated_data)
        
        container = get_container()
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
            order_id=order_id,
            **validated
        )
        
        container = get_container()
        try:
            response = container.manage_lines_use_case.add_line(command)
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
            order_id=order_id,
            product_id=product_id,
            **serializer.validated_data
        )
        
        container = get_container()
        try:
            response = container.manage_lines_use_case.update_line_quantity(command)
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
            order_id=order_id,
            **serializer.validated_data
        )
        
        container = get_container()
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
            order_id=order_id
        )
        
        container = get_container()
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
        container = get_container()
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
        container = get_container()
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
        container = get_container()
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
        container = get_container()
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
