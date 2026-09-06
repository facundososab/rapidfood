from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from modules.catalog.configuration.container import get_catalog_container
from modules.catalog.application.ports.driver.create_variant_ports import CreateVariantCommand
from modules.catalog.application.ports.driver.update_variant_ports import UpdateVariantCommand
from modules.catalog.application.ports.driver.set_variant_price_ports import SetVariantPriceCommand
from modules.catalog.application.ports.driver.create_ingredient_ports import CreateIngredientCommand
from modules.catalog.application.ports.driver.update_ingredient_ports import UpdateIngredientCommand
from modules.catalog.application.ports.driver.set_variant_ingredients_ports import (
    SetVariantIngredientsCommand, IngredientEntry,
)
from modules.catalog.application.ports.driver.create_modifier_group_ports import CreateModifierGroupCommand
from modules.catalog.application.ports.driver.update_modifier_group_ports import UpdateModifierGroupCommand
from modules.catalog.application.ports.driver.create_modifier_option_ports import CreateModifierOptionCommand
from modules.catalog.application.ports.driver.update_modifier_option_ports import UpdateModifierOptionCommand
from modules.catalog.domain.errors.catalog_errors import (
    DomainError, VariantNotFoundError, IngredientNotFoundError,
    ModifierGroupNotFoundError, ModifierOptionNotFoundError,
)
from .serializers_variants import (
    CreateVariantSerializer, UpdateVariantSerializer, SetVariantPriceSerializer,
    CreateIngredientSerializer, UpdateIngredientSerializer, SetVariantIngredientsSerializer,
    CreateModifierGroupSerializer, UpdateModifierGroupSerializer,
    CreateModifierOptionSerializer, UpdateModifierOptionSerializer,
)

class ProductVariantListView(APIView):
    """POST /api/catalog/products/<product_id>/variants/ — Create a variant."""
    def post(self, request, product_id):
        serializer = CreateVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.create_variant.execute(
                CreateVariantCommand(
                    product_id=str(product_id),
                    **serializer.validated_data,
                )
            )
            return Response(
                {"id": response.id, "name": response.name, "available": response.available,
                 "current_price": str(response.current_price)},
                status=status.HTTP_201_CREATED,
            )
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProductVariantDetailView(APIView):
    """PATCH /api/catalog/variants/<variant_id>/ — Update a variant."""
    def patch(self, request, variant_id):
        serializer = UpdateVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.update_variant.execute(
                UpdateVariantCommand(variant_id=str(variant_id), **serializer.validated_data)
            )
            return Response({"id": response.id, "name": response.name, "available": response.available})
        except VariantNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

class VariantPriceView(APIView):
    """POST /api/catalog/variants/<variant_id>/prices/ — Set variant price."""
    def post(self, request, variant_id):
        serializer = SetVariantPriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.set_variant_price.execute(
                SetVariantPriceCommand(
                    product_variant_id=str(variant_id),
                    **serializer.validated_data,
                )
            )
            return Response(
                {"price_id": response.price_id, "price": str(response.price), "since_date": str(response.since_date)},
                status=status.HTTP_201_CREATED,
            )
        except VariantNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

class IngredientListView(APIView):
    """GET /api/catalog/ingredients/ | POST /api/catalog/ingredients/"""
    def get(self, request):
        container = get_app_catalog_container()
        return Response(container.list_ingredients.execute())

    def post(self, request):
        serializer = CreateIngredientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        response = container.create_ingredient.execute(
            CreateIngredientCommand(**serializer.validated_data)
        )
        return Response({"id": response.id, "name": response.name}, status=status.HTTP_201_CREATED)

class IngredientDetailView(APIView):
    """PATCH /api/catalog/ingredients/<ingredient_id>/"""
    def patch(self, request, ingredient_id):
        serializer = UpdateIngredientSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.update_ingredient.execute(
                UpdateIngredientCommand(ingredient_id=str(ingredient_id), **serializer.validated_data)
            )
            return Response({"id": response.id, "name": response.name})
        except IngredientNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

class VariantIngredientsView(APIView):
    """PUT /api/catalog/variants/<variant_id>/ingredients/"""
    def put(self, request, variant_id):
        serializer = SetVariantIngredientsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            entries = [
                IngredientEntry(
                    ingredient_id=str(e["ingredient_id"]),
                    removable=e["removable"],
                )
                for e in serializer.validated_data["entries"]
            ]
            response = container.set_variant_ingredients.execute(
                SetVariantIngredientsCommand(variant_id=str(variant_id), entries=entries)
            )
            return Response({
                "variant_id": response.variant_id,
                "ingredients": [
                    {"id": i.id, "ingredient_id": i.ingredient_id, "name": i.name, "removable": i.removable}
                    for i in response.ingredients
                ],
            })
        except (VariantNotFoundError, IngredientNotFoundError) as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

class ModifierGroupListView(APIView):
    """POST /api/catalog/products/<product_id>/modifier-groups/"""
    def post(self, request, product_id):
        serializer = CreateModifierGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.create_modifier_group.execute(
                CreateModifierGroupCommand(product_id=str(product_id), **serializer.validated_data)
            )
            return Response(
                {"id": response.id, "name": response.name, "min_selections": response.min_selections,
                 "max_selections": response.max_selections},
                status=status.HTTP_201_CREATED,
            )
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ModifierGroupDetailView(APIView):
    """PATCH /api/catalog/modifier-groups/<group_id>/"""
    def patch(self, request, group_id):
        serializer = UpdateModifierGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.update_modifier_group.execute(
                UpdateModifierGroupCommand(group_id=str(group_id), **serializer.validated_data)
            )
            return Response({"id": response.id, "name": response.name,
                             "min_selections": response.min_selections, "max_selections": response.max_selections})
        except ModifierGroupNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

class ModifierOptionListView(APIView):
    """POST /api/catalog/modifier-groups/<group_id>/options/"""
    def post(self, request, group_id):
        serializer = CreateModifierOptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.create_modifier_option.execute(
                CreateModifierOptionCommand(
                    modifier_group_id=str(group_id),
                    **serializer.validated_data,
                )
            )
            return Response(
                {"id": response.id, "name": response.name, "price_delta": str(response.price_delta),
                 "available": response.available},
                status=status.HTTP_201_CREATED,
            )
        except ModifierGroupNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

class ModifierOptionDetailView(APIView):
    """PATCH /api/catalog/modifier-options/<option_id>/"""
    def patch(self, request, option_id):
        serializer = UpdateModifierOptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        container = get_app_catalog_container()
        try:
            response = container.update_modifier_option.execute(
                UpdateModifierOptionCommand(option_id=str(option_id), **serializer.validated_data)
            )
            return Response({"id": response.id, "name": response.name,
                             "price_delta": str(response.price_delta), "available": response.available})
        except ModifierOptionNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
