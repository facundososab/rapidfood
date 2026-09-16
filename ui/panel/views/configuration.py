import json
from decimal import Decimal

from django.http import HttpResponseBadRequest
from django.shortcuts import redirect

from .common import page
from ..services.factory import get_client


def index(request, tab='general'):
    client = get_client()
    business = client.get_business_config()
    delivery = None
    delivery_json = 'null'
    business_hours_json = '[]'

    if business and business.id:
        delivery = client.get_delivery_config(business.id)
        if delivery:
            delivery_json = json.dumps(delivery) if isinstance(delivery, dict) else 'null'

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

    return page(request, 'configuration/index.html', {
        'active_section': 'configuration',
        'active_tab': tab,
        'business': business,
        'delivery': delivery,
        'delivery_json': delivery_json,
        'business_hours_json': business_hours_json,
    })


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
        return HttpResponseBadRequest(f"Error saving hours: {str(e)}")

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

    return redirect('configuration_address_view')


def delete_address(request, address_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    business_id = request.POST.get('business_config_id', 'default')
    get_client().delete_business_address(business_id, address_id)
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
        return HttpResponseBadRequest(str(e))

    return redirect('configuration_delivery_view')
