from datetime import datetime
from decimal import Decimal
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page,required
from ..services.factory import get_client

def _ctx(request): return {'active_section':'coupons'}
def index(request): return page(request,'coupons/index.html',{**_ctx(request),'coupons':get_client().list_coupons()})
def form(request): return page(request,'coupons/form.html',_ctx(request))
def save(request):
 if request.method!='POST': return HttpResponseBadRequest()
 exp=request.POST.get('date_of_expiration')
 p={'couponCode':request.POST['coupon_code'].upper(),'type':request.POST['type'],'amount':Decimal(request.POST['amount']),'availableUses':int(request.POST['available_uses']),'dateOfExpiration':datetime.strptime(exp,'%Y-%m-%d') if exp else None}
 get_client().save_coupon(p); return redirect('coupons')
def detail(request,coupon_id):
 c=get_client(); coupon=required(c.get_coupon(coupon_id)); return page(request,'coupons/detail.html',{**_ctx(request),'coupon':coupon,'applied':c.list_applied_coupons(coupon_id=coupon_id)})
