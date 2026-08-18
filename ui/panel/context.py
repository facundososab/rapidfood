"""Template context processors shared across every page."""
from __future__ import annotations


NAV_ITEMS = [
    {"key": "dashboard", "label": "Dashboard", "url": "dashboard", "icon": "layout-dashboard"},
    {"key": "orders", "label": "Pedidos", "url": "orders", "icon": "receipt"},
    {"key": "products", "label": "Productos", "url": "products", "icon": "utensils"},
    {"key": "payments", "label": "Pagos", "url": "payments", "icon": "credit-card"},
    {"key": "clients", "label": "Clientes", "url": "clients", "icon": "users"},
    {"key": "coupons", "label": "Cupones", "url": "coupons", "icon": "ticket-percent"},
    {"key": "conversations", "label": "Conversaciones", "url": "conversations", "icon": "messages-square"},
]

SECONDARY_NAV = [
    {"key": "configuration", "label": "Configuración", "url": "configuration", "icon": "settings"},
]


def nav(request):
    return {
        "nav_items": NAV_ITEMS,
        "secondary_nav": SECONDARY_NAV,
        "active_section": getattr(request, "active_section", ""),
    }
