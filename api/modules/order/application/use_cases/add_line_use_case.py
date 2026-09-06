import uuid
from decimal import Decimal
from typing import List

from modules.order.application.ports.driver.add_line_port import (
    AddLinePort,
    AddLineCommand,
    AddLineResponse,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.catalog_query import CatalogQuery, VariantContext
from modules.order.domain.models.order_line import OrderLine
from modules.order.domain.models.order_line_modifier import OrderLineModifier
from modules.order.domain.models.order_line_removed_ingredient import OrderLineRemovedIngredient
from modules.order.domain.errors.order_errors import (
    OrderNotFound,
    InvalidLineError,
    IngredientNotRemovableError,
    ModifierValidationError,
)


def _validate_removed_ingredients(
    removed_ingredient_ids: List[str],
    context: VariantContext,
    line_id: str,
) -> List[OrderLineRemovedIngredient]:
    """Validate and build OrderLineRemovedIngredient list."""
    if not removed_ingredient_ids:
        return []

    # Check for duplicates
    if len(removed_ingredient_ids) != len(set(removed_ingredient_ids)):
        raise InvalidLineError("Duplicate removed ingredient IDs")

    ingredient_map = {ing.ingredient_id: ing for ing in context.ingredients}
    result = []
    for ing_id in removed_ingredient_ids:
        ing = ingredient_map.get(ing_id)
        if ing is None:
            raise InvalidLineError(
                f"Ingredient {ing_id} does not belong to variant {context.variant_id}"
            )
        if not ing.removable:
            raise IngredientNotRemovableError(
                f"Ingredient {ing.name} cannot be removed from this variant"
            )
        result.append(
            OrderLineRemovedIngredient(
                id=str(uuid.uuid4()),
                order_line_id=line_id,
                ingredient_id=ing_id,
                ingredient_name_snapshot=ing.name,
            )
        )
    return result


def _validate_modifiers(
    modifier_option_ids: List[str],
    context: VariantContext,
    line_id: str,
) -> List[OrderLineModifier]:
    """Validate and build OrderLineModifier list."""
    if not modifier_option_ids:
        return []

    # Check for duplicates
    if len(modifier_option_ids) != len(set(modifier_option_ids)):
        raise ModifierValidationError("Duplicate modifier option IDs")

    # Build lookup: option_id -> (group, option)
    option_lookup = {}
    for group in context.modifier_groups:
        for opt in group.options:
            option_lookup[opt.option_id] = (group, opt)

    # Validate each option and track per-group selections
    group_selection_counts: dict = {}
    result = []
    for opt_id in modifier_option_ids:
        entry = option_lookup.get(opt_id)
        if entry is None:
            raise ModifierValidationError(
                f"Modifier option {opt_id} does not belong to product {context.product_id}"
            )
        group, opt = entry
        if not opt.available:
            raise ModifierValidationError(f"Modifier option {opt.name} is not available")

        group_selection_counts[group.group_id] = group_selection_counts.get(group.group_id, 0) + 1
        result.append(
            OrderLineModifier(
                id=str(uuid.uuid4()),
                order_line_id=line_id,
                modifier_option_id=opt_id,
                option_name_snapshot=opt.name,
                price_delta=None,  # frozen at confirmation
            )
        )

    # Validate min/max per group
    for group in context.modifier_groups:
        count = group_selection_counts.get(group.group_id, 0)
        if count < group.min_selections:
            raise ModifierValidationError(
                f"Group '{group.name}' requires at least {group.min_selections} selection(s), got {count}"
            )
        if count > group.max_selections:
            raise ModifierValidationError(
                f"Group '{group.name}' allows at most {group.max_selections} selection(s), got {count}"
            )

    return result


class AddLineUseCase(AddLinePort):
    def __init__(self, order_repo: OrderRepository, catalog_query: CatalogQuery) -> None:
        self.order_repo = order_repo
        self.catalog_query = catalog_query

    def add_line(self, command: AddLineCommand) -> AddLineResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        context = self.catalog_query.get_variant_context(command.product_variant_id)
        if context is None:
            raise InvalidLineError(f"Variant {command.product_variant_id} not found")
        if not context.is_sellable:
            raise InvalidLineError(
                f"Variant {context.variant_name} of product {context.product_name} is not available"
            )

        line_id = str(uuid.uuid4())

        removed_ingredients = _validate_removed_ingredients(
            command.removed_ingredient_ids, context, line_id
        )
        modifiers = _validate_modifiers(
            command.modifier_option_ids, context, line_id
        )

        # Calculate price: variant base + sum of modifier deltas
        # (priceDelta from catalog, not from client input)
        option_lookup = {
            opt.option_id: opt
            for group in context.modifier_groups
            for opt in group.options
        }
        modifier_total = sum(
            option_lookup[opt_id].price_delta
            for opt_id in command.modifier_option_ids
        )
        unit_price = context.current_price + modifier_total
        subtotal = unit_price * command.quantity

        line = OrderLine(
            id=line_id,
            order_id=order.id,
            product_variant_id=context.variant_id,
            quantity=command.quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            modifiers=modifiers,
            removed_ingredients=removed_ingredients,
        )

        order.add_line(line)
        self.order_repo.save(order)

        return AddLineResponse(
            order_id=order.id,
            line_id=line_id,
            total_amount=str(order.total_amount),
            line_count=len(order.lines),
        )
