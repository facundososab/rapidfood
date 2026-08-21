from decimal import Decimal
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page
from ..services.factory import get_client

def index(request):
    client = get_client()
    business = client.get_business_config()
    delivery = None
    if business and business.id:
        delivery = client.get_delivery_config(business.id)
    return page(request, 'configuration/index.html', {
        'active_section': 'configuration',
        'business': business,
        'delivery': delivery,
    })

def save_general(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    get_client().save_business_config({
        'businessName': request.POST.get('business_name'),
        'minOrder': Decimal(request.POST['min_order']),
        'shippingCost': Decimal(request.POST['shipping_cost']),
        'availableZone': request.POST.get('available_zone')
    })
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
            "demand_window_minutes": int(request.POST.get("demand_window_minutes", 60)),
            "high_demand_multiplier": request.POST.get("high_demand_multiplier"),
            "very_high_demand_multiplier": request.POST.get("very_high_demand_multiplier"),
            "weekday_multipliers": weekday_multipliers
        }
        get_client().save_delivery_config(business_id, payload)
    except Exception as e:
        return HttpResponseBadRequest(str(e))
        
    return redirect('configuration')
