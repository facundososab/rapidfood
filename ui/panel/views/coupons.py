from datetime import datetime
from decimal import Decimal
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page,required
from ..services.factory import get_client

def _ctx(request): return {'active_section':'coupons'}
def index(request): return page(request,'coupons/index.html',{**_ctx(request),'coupons':get_client().list_coupons()})
def form(request): return redirect('coupons')  # creation is a modal on the list
def save(request):
 if request.method!='POST': return HttpResponseBadRequest()
 exp=request.POST.get('date_of_expiration')
 min_order=request.POST.get('min_order_amount')
 p={'couponCode':request.POST['coupon_code'].upper(),'type':request.POST['type'],'amount':Decimal(request.POST['amount']),'availableUses':int(request.POST['available_uses']),'minOrderAmount':Decimal(min_order) if min_order else None,'dateOfExpiration':datetime.strptime(exp,'%Y-%m-%d') if exp else None}
 get_client().save_coupon(p); return redirect('coupons')
def detail(request,coupon_id):
 c=get_client(); coupon=required(c.get_coupon(coupon_id)); return page(request,'coupons/detail.html',{**_ctx(request),'coupon':coupon,'applied':c.list_applied_coupons(coupon_id=coupon_id)})
def update(request,coupon_id):
 if request.method!='POST': return HttpResponseBadRequest()
 exp=request.POST.get('date_of_expiration')
 min_order=request.POST.get('min_order_amount')
 uses=request.POST.get('available_uses')
 p={'amount':Decimal(request.POST['amount']),
    'availableUses':int(uses) if uses else None,
    'minOrderAmount':Decimal(min_order) if min_order else None,
    'dateOfExpiration':datetime.strptime(exp,'%Y-%m-%d') if exp else None,
    'isActive':request.POST.get('is_active')=='on'}
 get_client().update_coupon(coupon_id,p); return redirect('coupon_detail',coupon_id=coupon_id)
def toggle(request,coupon_id):
 if request.method!='POST': return HttpResponseBadRequest()
 c=get_client().get_coupon(coupon_id)
 new_state=not c.isActive
 get_client().set_coupon_active(coupon_id,new_state)
 messages.success(request,'Cupón activado.' if new_state else 'Cupón pausado.')
 return redirect('coupon_detail',coupon_id=coupon_id)
