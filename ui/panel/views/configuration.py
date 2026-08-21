from decimal import Decimal
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page
from ..services.factory import get_client

def index(request):
    import json
    from decimal import Decimal

    client = get_client()
    business = client.get_business_config()
    delivery = None
    delivery_json = 'null'
    if business and business.id:
        delivery = client.get_delivery_config(business.id)
        if delivery:
            # Make it JSON-serializable for Alpine.js (Decimals → strings)
            def _safe(v):
                if isinstance(v, Decimal):
                    return str(v)
                return v
            delivery_json = json.dumps(delivery) if isinstance(delivery, dict) else 'null'

    return page(request, 'configuration/index.html', {
        'active_section': 'configuration',
        'business': business,
        'delivery': delivery,
        'delivery_json': delivery_json,
    })


def save_general(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    business_id = request.POST.get('business_config_id', 'default')
    
    # Save basic config
    get_client().save_business_config({
        'businessName': request.POST.get('business_name'),
        'minOrder': Decimal(request.POST['min_order']),
        'shippingCost': Decimal(request.POST['shipping_cost']),
        'availableZone': request.POST.get('available_zone')
    })
    
    # Save hours
    import json
    try:
        hours_json = request.POST.get('business_hours', '[]')
        hours = json.loads(hours_json)
        if hours:
            get_client().save_business_hours(business_id, hours)
    except Exception as e:
        pass # Handle properly in prod
        
    return redirect('configuration')

def create_address(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()
        
    business_id = request.POST.get('business_config_id', 'default')
    payload = {
        'street': request.POST.get('street'),
        'streetNumber': request.POST.get('street_number'),
        'city': request.POST.get('city'),
        'province': request.POST.get('province'),
        'postalCode': request.POST.get('postal_code'),
        'floor': request.POST.get('floor'),
        'apartment': request.POST.get('apartment'),
    }
    
    get_client().create_business_address(business_id, payload)
    return redirect('configuration')

def delete_address(request, address_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()
        
    business_id = request.POST.get('business_config_id', 'default')
    get_client().delete_business_address(business_id, address_id)
    return redirect('configuration')

def save_delivery(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    import json
    business_id = request.POST.get("business_config_id")
    if not business_id:
        return HttpResponseBadRequest("Missing business_config_id")
    
    try:
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
            "weekday_multipliers": weekday_multipliers
        }
        get_client().save_delivery_config(business_id, payload)
    except Exception as e:
        return HttpResponseBadRequest(str(e))
        
    return redirect('configuration')
