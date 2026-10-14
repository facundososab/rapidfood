"""Public customer-facing menu page ("carta digital")."""
from __future__ import annotations

import re

from django.shortcuts import render

from ..services.public_menu import get_public_contact, get_public_menu


def carta(request):
    menu = get_public_menu()
    contact = get_public_contact()
    return render(
        request,
        "menu/index.html",
        {
            "menu": menu,
            "contact": contact,
            "whatsapp_url": _whatsapp_url(contact.whatsapp_number),
            "title": contact.business_name or "Nuestra Carta",
        },
    )


def _whatsapp_url(number) -> str | None:
    if not number:
        return None
    digits = re.sub(r"\D", "", str(number))
    return f"https://wa.me/{digits}" if digits else None
