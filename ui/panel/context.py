"""Template context processors shared across every page."""
from __future__ import annotations


NAV_ITEMS = [
    {"key": "dashboard", "label": "Dashboard", "url": "dashboard", "icon": "layout-dashboard"},
    {
        "key": "orders",
        "label": "Pedidos",
        "url": "orders",
        "icon": "receipt",
        "children": [
            {"key": "orders-list", "label": "Listado", "url": "orders_listing"},
        ],
    },
    {"key": "kitchen", "label": "Cocina", "url": "kitchen", "icon": "chef-hat"},
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
        "staff_user": _staff_user(request),
    }


ROLE_LABELS = {
    "ADMIN": "Administrador",
    "CASHIER": "Caja",
    "KITCHEN": "Cocina",
}


def _staff_user(request):
    """Current operator from the session (email + optional staff profile)."""
    profile = request.session.get("supabase_staff")
    email = request.session.get("supabase_email") or ""
    if not profile and not email:
        return None
    name = (profile or {}).get("name") or email
    role = (profile or {}).get("role")
    return {
        "display_name": name,
        "email": email,
        "role_label": ROLE_LABELS.get(role, "Personal") if role else "Personal",
        "initials": _initials(name),
    }


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "RF"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()
