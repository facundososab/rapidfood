"""Thin LangChain tools for the Rapidfood agent.

Each tool only maps its arguments to a conversation command, runs the use case
with the TRUSTED context (captured in the closure, never a tool argument) and
serializes the result. No business rules here.

Results are JSON strings:
    {"ok": true,  "data": {...}}
    {"ok": false, "error": {"code": "...", "message": "..."}}

Business errors carry a stable code the agent can explain; any other exception
becomes a generic technical error (never a stack trace, never a business claim).
"""
from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any, Literal, Optional

from langchain_core.tools import BaseTool, tool

from modules.conversation.domain.models.agent_execution_context import (
    AgentExecutionContext,
)
from modules.conversation.application.ports.driver.agent_commands import (
    AddItemCommand,
    AddressCommand,
    ApplyCouponCommand,
    SetClientCommand,
    GetProductDetailQuery,
    QuoteDeliveryQuery,
    RemoveItemCommand,
    SearchProductsQuery,
    SetDeliveryCommand,
    SetPaymentTypeCommand,
    UpdateItemCommand,
)
from modules.conversation.domain.errors import AgentBusinessError

TECHNICAL_ERROR_MESSAGE = (
    "No pude procesar eso en este momento. ¿Podés intentar de nuevo?"
)

logger = logging.getLogger(__name__)


def _dump(value: Any) -> str:
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    return json.dumps(value, default=str, ensure_ascii=False)


def _run(operation) -> str:
    try:
        return _dump({"ok": True, "data": operation()})
    except AgentBusinessError as exc:
        return _dump(
            {"ok": False, "error": {"code": exc.code, "message": str(exc)}}
        )
    except Exception:
        # Technical failure: no stack trace to the customer, but keep the cause
        # in the server logs so it can be diagnosed.
        logger.exception("Agent tool failed")
        return _dump(
            {
                "ok": False,
                "error": {"code": "TECHNICAL_ERROR", "message": TECHNICAL_ERROR_MESSAGE},
            }
        )


def _address(
    street: str,
    street_number: str,
    city: str,
    province: str,
    floor: Optional[str],
    apartment: Optional[str],
    postal_code: Optional[str],
) -> AddressCommand:
    return AddressCommand(
        street=street,
        street_number=street_number,
        city=city,
        province=province,
        floor=floor,
        apartment=apartment,
        postal_code=postal_code,
    )


def build_tools(
    container: Any,
    context: AgentExecutionContext,
    turn_state: Optional[dict] = None,
) -> list[BaseTool]:
    """Build the agent tools bound to one trusted execution context.

    ``turn_state`` is an optional mutable per-turn holder the adapter uses to
    remember side effects it must validate afterwards (e.g. the REAL
    checkout_url), so a hallucinated payment link can be caught and replaced.
    """

    @tool
    def search_products(query: Optional[str] = None) -> str:
        """Busca productos del menú por texto. Busca en el nombre del producto, su
        descripción y el nombre de cada variante, así que sirve tanto para
        "Classic Burger" como para "Classic Burger Doble" o "Coca-Cola 500".
        Devuelve cada producto con sus variantes y el precio de cada una: usalo
        para responder precios sin otra consulta. Sin texto devuelve el menú
        completo (evitalo si podés acotar con palabras)."""
        return _run(
            lambda: container.search_products_use_case.execute(
                SearchProductsQuery(query=query), context
            )
        )

    @tool
    def get_product_detail(product_id: str) -> str:
        """Devuelve el detalle de un producto: variantes, precios actuales,
        ingredientes (y si se pueden quitar) y grupos de modificadores."""
        return _run(
            lambda: container.get_product_detail_use_case.execute(
                GetProductDetailQuery(product_id=product_id), context
            )
        )

    @tool
    def get_current_order() -> str:
        """Devuelve el pedido actual de esta conversación y si se puede modificar.
        Usalo para saber qué hay en el carrito; no lo reconstruyas del historial."""
        return _run(
            lambda: container.get_current_order_use_case.execute(context)
        )

    @tool
    def add_item(
        product_variant_id: str,
        quantity: int,
        modifier_option_ids: Optional[list[str]] = None,
        removed_ingredient_ids: Optional[list[str]] = None,
    ) -> str:
        """Agrega un producto al pedido actual (crea el borrador si no existe).
        No envíes precios: los calcula el backend."""
        return _run(
            lambda: container.add_item_use_case.execute(
                AddItemCommand(
                    product_variant_id=product_variant_id,
                    quantity=quantity,
                    modifier_option_ids=tuple(modifier_option_ids or ()),
                    removed_ingredient_ids=tuple(removed_ingredient_ids or ()),
                ),
                context,
            )
        )

    @tool
    def update_item(
        line_id: str,
        quantity: Optional[int] = None,
        modifier_option_ids: Optional[list[str]] = None,
        removed_ingredient_ids: Optional[list[str]] = None,
    ) -> str:
        """Modifica una línea del pedido por su line_id. Para quitar todos los
        modificadores o ingredientes mandá una lista vacía []; para no cambiarlos, omitilos."""
        return _run(
            lambda: container.update_item_use_case.execute(
                UpdateItemCommand(
                    line_id=line_id,
                    quantity=quantity,
                    modifier_option_ids=(
                        tuple(modifier_option_ids)
                        if modifier_option_ids is not None
                        else None
                    ),
                    removed_ingredient_ids=(
                        tuple(removed_ingredient_ids)
                        if removed_ingredient_ids is not None
                        else None
                    ),
                ),
                context,
            )
        )

    @tool
    def remove_item(line_id: str) -> str:
        """Quita una línea completa del pedido por su line_id."""
        return _run(
            lambda: container.remove_item_use_case.execute(
                RemoveItemCommand(line_id=line_id), context
            )
        )

    @tool
    def quote_delivery(
        street: str,
        street_number: str,
        city: Optional[str] = None,
        province: Optional[str] = None,
        floor: Optional[str] = None,
        apartment: Optional[str] = None,
        postal_code: Optional[str] = None,
    ) -> str:
        """Consulta si se entrega en una dirección y cuánto cuesta el envío.
        Alcanza con calle y número (la ciudad y la provincia son las del local).
        No crea ni modifica pedidos."""
        return _run(
            lambda: container.quote_delivery_use_case.execute(
                QuoteDeliveryQuery(
                    address=_address(
                        street, street_number, city, province, floor, apartment, postal_code
                    )
                ),
                context,
            )
        )

    @tool
    def set_delivery(
        street: str,
        street_number: str,
        city: Optional[str] = None,
        province: Optional[str] = None,
        floor: Optional[str] = None,
        apartment: Optional[str] = None,
        postal_code: Optional[str] = None,
    ) -> str:
        """Configura el envío del pedido a una dirección. Alcanza con calle y
        número. El backend cotiza el costo; si la dirección está fuera de zona, el
        pedido no se modifica."""
        return _run(
            lambda: container.set_delivery_use_case.execute(
                SetDeliveryCommand(
                    address=_address(
                        street, street_number, city, province, floor, apartment, postal_code
                    )
                ),
                context,
            )
        )

    @tool
    def set_pickup() -> str:
        """Configura el pedido para retiro en el local (sin envío)."""
        return _run(lambda: container.set_pickup_use_case.execute(context))

    @tool
    def set_client(name: str, phone_number: Optional[str] = None) -> str:
        """Guarda el nombre del cliente en el pedido y, si dio un teléfono, lo
        asocia a su ficha. Usalo apenas el cliente diga su nombre (siempre antes
        de pedir la confirmación)."""
        return _run(
            lambda: container.set_client_use_case.execute(
                SetClientCommand(name=name, phone_number=phone_number), context
            )
        )

    @tool
    def set_payment_type(payment_type: Literal["CASH", "ONLINE"]) -> str:
        """Define la forma de pago del pedido: CASH (efectivo) u ONLINE (pago
        online con link). Si el cliente dice "Mercado Pago", "MP", "pagame con
        link", "pago online" o "mandame el link", la forma de pago es ONLINE.
        Mercado Pago NO es una forma de pago aparte: se traduce siempre a ONLINE."""
        return _run(
            lambda: container.set_payment_type_use_case.execute(
                SetPaymentTypeCommand(payment_type=payment_type), context
            )
        )

    @tool
    def apply_coupon(coupon_code: str) -> str:
        """Aplica un cupón al pedido. La validez y el descuento los decide el backend."""
        return _run(
            lambda: container.apply_coupon_use_case.execute(
                ApplyCouponCommand(coupon_code=coupon_code), context
            )
        )

    @tool
    def get_order_summary() -> str:
        """Resumen confiable del pedido actual: líneas, subtotal, descuento, envío,
        total, forma de pago y qué falta. Usalo antes de pedir confirmación."""
        return _run(
            lambda: container.get_order_summary_use_case.execute(context)
        )

    @tool
    def confirm_order() -> str:
        """Confirma el pedido actual. Llamala SOLO después de mostrar el resumen y
        de que el cliente confirme explícitamente ESE resumen."""
        return _run(lambda: container.confirm_order_use_case.execute(context))

    @tool
    def cancel_order() -> str:
        """Cancela el pedido activo. Las reglas de cancelación las decide el backend."""
        return _run(lambda: container.cancel_order_use_case.execute(context))

    @tool
    def create_payment_checkout() -> str:
        """Genera el link de pago del pedido actual (solo pedidos ONLINE ya
        confirmados). Usalo después de la confirmación explícita; el link lo crea
        el backend. Copiá el checkout_url que devuelve: es el ÚNICO link válido."""

        def operation():
            result = container.create_checkout_use_case.execute(context)
            if turn_state is not None:
                turn_state["checkout_url"] = getattr(result, "checkout_url", None)
            return result

        return _run(operation)

    @tool
    def get_latest_active_order() -> str:
        """Devuelve el último pedido activo del cliente (para "¿cómo viene mi pedido?")."""
        return _run(
            lambda: container.get_latest_active_order_use_case.execute(context)
        )

    @tool
    def get_menu_link() -> str:
        """Devuelve el link público de la carta digital (el menú con precios).
        Usala cuando el cliente pida ver la carta o el menú, o pida un link para
        verlo. Compartí EXACTAMENTE la URL que devuelve: nunca la escribas de memoria
        ni inventes el dominio."""

        def operation():
            base = (getattr(container, "menu_public_url", None) or "").rstrip("/")
            if not base:
                raise AgentBusinessError(
                    "No tengo el link de la carta disponible en este momento.",
                    code="MENU_LINK_UNAVAILABLE",
                )
            url = f"{base}/carta/"
            if turn_state is not None:
                turn_state["menu_url"] = url
            return {"menu_url": url}

        return _run(operation)

    return [
        search_products,
        get_product_detail,
        get_current_order,
        add_item,
        update_item,
        remove_item,
        quote_delivery,
        set_delivery,
        set_pickup,
        set_client,
        set_payment_type,
        apply_coupon,
        get_order_summary,
        confirm_order,
        cancel_order,
        create_payment_checkout,
        get_latest_active_order,
        get_menu_link,
    ]
