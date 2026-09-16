from decimal import Decimal
from datetime import datetime

from modules.order.application.ports.driver.confirm_order_ports import (
    ConfirmOrderPort,
    ConfirmOrderCommand,
    ConfirmOrderResponse,
)
from modules.order.application.ports.driven.order_repository import OrderRepository
from modules.order.application.ports.driven.business_config_query import BusinessConfigQueryPort
from modules.order.application.ports.driven.catalog_query import CatalogQuery
from modules.order.domain.errors.order_errors import (
    OrderNotFound,
    OrderNotModifiableError,
    BusinessClosedError,
    MinimumOrderNotMetError,
    InvalidLineError,
    IngredientNotRemovableError,
    ModifierValidationError,
)
from modules.order.domain.models.order_state import OrderState


class ConfirmOrderUseCase(ConfirmOrderPort):
    def __init__(
        self,
        order_repo: OrderRepository,
        config_query: BusinessConfigQueryPort,
        catalog_query: CatalogQuery,
    ) -> None:
        self.order_repo = order_repo
        self.config_query = config_query
        self.catalog_query = catalog_query

    def execute(self, command: ConfirmOrderCommand) -> ConfirmOrderResponse:
        order = self.order_repo.get_by_id(command.order_id)
        if not order:
            raise OrderNotFound("Order not found")

        if order.status != OrderState.DRAFT:
            raise OrderNotModifiableError("Only DRAFT orders can be confirmed")

        if not order.lines:
            raise InvalidLineError("Cannot confirm an empty order")

        # Business availability check
        config = self.config_query.get_config()
        if not config.is_open:
            raise BusinessClosedError("Business is currently closed")

        if order.subtotal < config.min_order_amount:
            raise MinimumOrderNotMetError(
                f"Minimum order amount is {config.min_order_amount}"
            )

        # Validate and freeze each line
        for line in order.lines:
            context = self.catalog_query.get_variant_context(line.product_variant_id)
            if context is None or not context.is_sellable:
                raise InvalidLineError(
                    f"Variant {line.product_variant_id} is no longer available"
                )

            # Validate removed ingredients are still removable
            ingredient_map = {ing.ingredient_id: ing for ing in context.ingredients}
            for removed in line.removed_ingredients:
                ing = ingredient_map.get(removed.ingredient_id)
                if ing is None:
                    raise InvalidLineError(
                        f"Ingredient {removed.ingredient_id} no longer belongs to this variant"
                    )
                if not ing.removable:
                    raise IngredientNotRemovableError(
                        f"Ingredient {ing.name} is no longer removable"
                    )
                # Freeze name snapshot
                removed.ingredient_name_snapshot = ing.name

            # Validate modifiers and freeze snapshots
            option_lookup = {
                opt.option_id: opt
                for group in context.modifier_groups
                for opt in group.options
            }
            group_selection_counts: dict = {}
            modifier_total = Decimal("0")
            for modifier in line.modifiers:
                opt = option_lookup.get(modifier.modifier_option_id)
                if opt is None:
                    raise ModifierValidationError(
                        f"Modifier option {modifier.modifier_option_id} is no longer valid"
                    )
                if not opt.available:
                    raise ModifierValidationError(
                        f"Modifier option {opt.name} is no longer available"
                    )
                # Freeze snapshots
                modifier.option_name_snapshot = opt.name
                modifier.price_delta = opt.price_delta
                modifier_total += opt.price_delta

                # Track group counts for min/max validation
                # Find group for this option
                for group in context.modifier_groups:
                    if any(o.option_id == modifier.modifier_option_id for o in group.options):
                        group_selection_counts[group.group_id] = (
                            group_selection_counts.get(group.group_id, 0) + 1
                        )
                        break

            # Validate group min/max
            for group in context.modifier_groups:
                count = group_selection_counts.get(group.group_id, 0)
                if count < group.min_selections:
                    raise ModifierValidationError(
                        f"Group '{group.name}' requires at least {group.min_selections} selection(s)"
                    )
                if count > group.max_selections:
                    raise ModifierValidationError(
                        f"Group '{group.name}' allows at most {group.max_selections} selection(s)"
                    )

            # Freeze prices
            configured_unit_price = context.current_price + modifier_total
            line.unit_price = configured_unit_price
            line.subtotal = configured_unit_price * line.quantity

        # Recalculate order totals with frozen line prices
        order._recalculate_totals()

        # Transition state and record confirmation time via domain method
        order.confirm()

        self.order_repo.save(order)

        return ConfirmOrderResponse(
            order_id=order.id,
            status=order.status.value,
            confirmed_at=order.confirmed_at.isoformat(),
        )
