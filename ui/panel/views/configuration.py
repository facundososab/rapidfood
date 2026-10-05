import json
from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect

from .common import page
from ..services.factory import get_client


def _staff_role(request):
    """Raw role from the session staff profile, or None when absent."""
    return (request.session.get('supabase_staff') or {}).get('role')


def index(request, tab='general'):
    client = get_client()
    business = client.get_business_config()
    delivery = None
    delivery_json = 'null'
    prep_time = None
    prep_time_json = 'null'
    business_hours_json = '[]'
    whatsapp = {'configured': False}

    if business and business.id:
        delivery = client.get_delivery_config(business.id)
        if delivery:
            delivery_json = json.dumps(delivery) if isinstance(delivery, dict) else 'null'

        prep_time = client.get_preparation_time_config(business.id)
        if prep_time:
            prep_time_json = json.dumps(prep_time) if isinstance(prep_time, dict) else 'null'

        whatsapp = client.get_whatsapp_config(business.id)

        if business.businessHours:
            bh = [
                {
                    'openWeekDay': h.openWeekDay,
                    'openFromHour': h.openFromHour,
                    'openToHour': h.openToHour,
                }
                for h in business.businessHours
            ]
            business_hours_json = json.dumps(bh)

    context = {
        'active_section': 'configuration',
        'active_tab': tab,
        'business': business,
        'delivery': delivery,
        'delivery_json': delivery_json,
        'prep_time': prep_time,
        'prep_time_json': prep_time_json,
        'business_hours_json': business_hours_json,
        'whatsapp': whatsapp,
        'is_mercadopago_admin': _staff_role(request) == 'ADMIN',
    }

    if tab == 'payments':
        context['mercadopago_status'] = client.get_mercadopago_status()

    return page(request, 'configuration/index.html', context)


def mercadopago_link(request):
    """Start the OAuth flow: redirect the ADMIN to Mercado Pago's authorization page."""
    if request.method != 'POST':
        return HttpResponseBadRequest()

    if _staff_role(request) != 'ADMIN':
        return HttpResponseForbidden()

    client = get_client()
    business_config_id = client.get_business_config().id
    url = client.get_mercadopago_authorization_url(business_config_id)
    if url:
        return redirect(url)

    messages.error(request, 'No se pudo iniciar la vinculación con Mercado Pago.')
    return redirect('configuration_payments_view')


def mercadopago_unlink(request):
    """Disconnect the business Mercado Pago account (idempotent on the backend)."""
    if request.method != 'POST':
        return HttpResponseBadRequest()

    if _staff_role(request) != 'ADMIN':
        return HttpResponseForbidden()

    client = get_client()
    business_config_id = client.get_business_config().id
    client.unlink_mercadopago(business_config_id)
    messages.success(request, 'Cuenta de Mercado Pago desvinculada')
    return redirect('configuration_payments_view')


def save_general(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    business_id = request.POST.get('business_config_id', 'default')
    client = get_client()
    business = client.get_business_config()

    client.save_business_config({
        'businessName': request.POST.get('business_name'),
        'minOrder': business.minOrder if business else Decimal('0'),
        'shippingCost': business.shippingCost if business else Decimal('0'),
        'availableZone': business.availableZone if business else None,
    })

    try:
        hours = json.loads(request.POST.get('business_hours', '[]'))
        if hours:
            get_client().save_business_hours(business_id, hours)
    except Exception as e:
        messages.error(request, f"No se pudo guardar: {e}")
        return redirect('configuration')

    messages.success(request, 'Datos del negocio guardados.')
    return redirect('configuration')


def create_address(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    business_id = request.POST.get('business_config_id', 'default')
    client = get_client()

    payload = {
        'street': request.POST.get('street'),
        'streetNumber': request.POST.get('street_number'),
        'city': request.POST.get('city'),
        'province': request.POST.get('province'),
        'postalCode': request.POST.get('postal_code'),
        'floor': request.POST.get('floor'),
        'apartment': request.POST.get('apartment'),
    }

    # Always derive the existing address from the DB — never trust a form-supplied address_id.
    # This enforces one address per business and prevents accidental duplicates.
    business = client.get_business_config()
    existing_address = business.addresses[0] if business and business.addresses else None

    if existing_address:
        client.update_business_address(business_id, existing_address.id, payload)
    else:
        client.create_business_address(business_id, payload)

    messages.success(request, 'Dirección guardada.')
    return redirect('configuration_address_view')


def delete_address(request, address_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    business_id = request.POST.get('business_config_id', 'default')
    get_client().delete_business_address(business_id, address_id)
    messages.success(request, 'Dirección eliminada.')
    return redirect('configuration_address_view')


def save_delivery(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    business_id = request.POST.get("business_config_id")
    if not business_id:
        return HttpResponseBadRequest("Missing business_config_id")

    try:
        client = get_client()
        business = client.get_business_config()
        if business:
            client.save_business_config({
                'businessName': business.businessName,
                'minOrder': Decimal(request.POST.get('min_order', business.minOrder)),
                'shippingCost': Decimal(request.POST.get('base_shipping_cost', business.shippingCost)),
                'availableZone': business.availableZone,
            })

        delivery_zone = json.loads(request.POST.get("delivery_zone", "{}"))
        weekday_multipliers = json.loads(request.POST.get("weekday_multipliers", "[]"))

        payload = {
            "base_shipping_cost": request.POST.get("base_shipping_cost"),
            "origin_address_id": request.POST.get("origin_address_id"),
            "delivery_zone": delivery_zone,
            "price_per_km": request.POST.get("price_per_km") or None,
            "high_demand_threshold": int(request.POST.get("high_demand_threshold", 0)),
            "very_high_demand_threshold": int(request.POST.get("very_high_demand_threshold", 0)),
            "high_demand_multiplier": request.POST.get("high_demand_multiplier"),
            "very_high_demand_multiplier": request.POST.get("very_high_demand_multiplier"),
            "weekday_multipliers": weekday_multipliers,
        }
        get_client().save_delivery_config(business_id, payload)
    except Exception as e:
        messages.error(request, f"No se pudo guardar envíos: {e}")
        return redirect('configuration_delivery_view')

    messages.success(request, 'Configuración de envíos guardada.')
    return redirect('configuration_delivery_view')


def save_preparation_time(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    business_id = request.POST.get("business_config_id")
    if not business_id:
        return HttpResponseBadRequest("Missing business_config_id")

    try:
        payload = {
            "high_demand_threshold": int(request.POST.get("high_demand_threshold", 0)),
            "very_high_demand_threshold": int(
                request.POST.get("very_high_demand_threshold", 0)
            ),
            "normal_prep_minutes": int(request.POST.get("normal_prep_minutes", 0)),
            "high_demand_prep_minutes": int(
                request.POST.get("high_demand_prep_minutes", 0)
            ),
            "very_high_demand_prep_minutes": int(
                request.POST.get("very_high_demand_prep_minutes", 0)
            ),
            "buffer_minutes": int(request.POST.get("buffer_minutes", 0)),
        }
        get_client().save_preparation_time_config(business_id, payload)
    except Exception as e:
        messages.error(request, f"No se pudieron guardar los tiempos: {e}")
        return redirect('configuration_prep_time_view')

    messages.success(request, 'Tiempos de preparación guardados.')
    return redirect('configuration_prep_time_view')


def _clean(value):
    value = (value or '').strip()
    return value or None


def save_whatsapp(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    business_id = request.POST.get("business_config_id")
    if not business_id:
        return HttpResponseBadRequest("Missing business_config_id")

    payload = {
        "phone_number_id": request.POST.get("phone_number_id", "").strip(),
        "verify_token": request.POST.get("verify_token", "").strip(),
        "access_token": _clean(request.POST.get("access_token")) or "",
        "app_secret": _clean(request.POST.get("app_secret")) or "",
        "api_version": _clean(request.POST.get("api_version")) or "v21.0",
        "waba_id": _clean(request.POST.get("waba_id")),
        "display_phone_number": _clean(request.POST.get("display_phone_number")),
        "order_paid_template_name": _clean(request.POST.get("order_paid_template_name")),
        "order_paid_template_lang": _clean(request.POST.get("order_paid_template_lang")) or "es_AR",
        "is_active": request.POST.get("is_active") == "on",
    }
    try:
        get_client().save_whatsapp_config(business_id, payload)
    except Exception as e:
        messages.error(request, f"No se pudo guardar WhatsApp: {e}")
        return redirect('configuration_whatsapp_view')

    messages.success(request, "Configuración de WhatsApp guardada.")
    return redirect('configuration_whatsapp_view')
