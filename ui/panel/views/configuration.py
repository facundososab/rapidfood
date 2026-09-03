from decimal import Decimal
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page
from ..services.factory import get_client

def index(request): return page(request,'configuration/index.html',{'active_section':'configuration','business':get_client().get_business_config()})
def save_general(request):
 if request.method!='POST': return HttpResponseBadRequest()
 get_client().save_business_config({'businessName':request.POST.get('business_name'),'minOrder':Decimal(request.POST['min_order']),'shippingCost':Decimal(request.POST['shipping_cost']),'availableZone':request.POST.get('available_zone')}); return redirect('configuration')
