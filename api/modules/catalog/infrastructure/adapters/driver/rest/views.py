from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.catalog.application.ports.driver.add_price_ports import AddPriceCommand
from modules.catalog.application.ports.driver.create_category_ports import (
    CreateCategoryCommand,
)
from modules.catalog.application.ports.driver.create_product_ports import (
    CreateProductCommand,
)
from modules.catalog.application.ports.driver.list_prices_ports import ListPricesQuery
from modules.catalog.application.ports.driver.list_products_ports import (
    ListProductsQuery,
)
from modules.catalog.application.ports.driver.set_discount_ports import SetDiscountCommand
from modules.catalog.application.ports.driver.set_product_state_ports import (
    SetProductStateCommand,
)
from modules.catalog.configuration.container import get_catalog_container
from modules.catalog.domain.errors.catalog_errors import (
    CategoryNotFoundError,
    ProductNotFoundError,
)
from modules.catalog.domain.models.product import ProductState

from .serializers import (
    AddPriceSerializer,
    CreateCategorySerializer,
    CreateProductSerializer,
    SetDiscountSerializer,
    SetProductStateSerializer,
)


class ProductListCreateView(APIView):
    def get(self, request):
        category_id = request.query_params.get("category_id")
        available_param = request.query_params.get("available")

        state = None
        if available_param is not None:
            state = (
                ProductState.AVAILABLE
                if available_param.lower() == "true"
                else ProductState.UNAVAILABLE
            )

        query = ListProductsQuery(category_id=category_id, state=state)
        results = get_catalog_container().list_products.execute(query)

        return Response([r.__dict__ for r in results])

    def post(self, request):
        serializer = CreateProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreateProductCommand(**serializer.validated_data)

        try:
            result = get_catalog_container().create_product.execute(command)
        except CategoryNotFoundError:
            return Response(
                {"detail": "La categoria no existe"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(result.__dict__, status=status.HTTP_201_CREATED)


class SetProductStateView(APIView):
    def patch(self, request, product_id: str):
        serializer = SetProductStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        state = ProductState(serializer.validated_data["state"])
        command = SetProductStateCommand(product_id=product_id, state=state)

        try:
            result = get_catalog_container().set_product_state.execute(command)
        except ProductNotFoundError:
            return Response(
                {"detail": "El producto no existe"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(result.__dict__)


class PriceListCreateView(APIView):
    def get(self, request, product_id: str):
        query = ListPricesQuery(product_id=product_id)
        results = get_catalog_container().list_prices.execute(query)

        return Response([r.__dict__ for r in results])

    def post(self, request, product_id: str):
        serializer = AddPriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = AddPriceCommand(product_id=product_id, **serializer.validated_data)

        try:
            result = get_catalog_container().add_price.execute(command)
        except ProductNotFoundError:
            return Response(
                {"detail": "El producto no existe"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(result.__dict__, status=status.HTTP_201_CREATED)


class CreateCategoryView(APIView):
    def post(self, request):
        serializer = CreateCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreateCategoryCommand(**serializer.validated_data)
        result = get_catalog_container().create_category.execute(command)

        return Response(result.__dict__, status=status.HTTP_201_CREATED)


class SetDiscountView(APIView):
    def post(self, request):
        serializer = SetDiscountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = SetDiscountCommand(**serializer.validated_data)

        try:
            result = get_catalog_container().set_discount.execute(command)
        except ProductNotFoundError:
            return Response(
                {"detail": "El producto no existe"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(result.__dict__, status=status.HTTP_201_CREATED)