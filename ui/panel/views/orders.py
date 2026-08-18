from decimal import Decimal
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page, required, int_param
from ..services.factory import get_client
from ..services import dtos
from ..domain import pricing

def _ctx(request):
    c=get_client(); return {'active_section':'orders','statuses':dtos.ORDER_STATUS_LABELS,'delivery_types':dtos.DELIVERY_TYPE_LABELS,'payment_types':dtos.PAYMENT_TYPE_LABELS,'client':c}
def index(request):
    return page(request,'orders/index.html',_list_ctx(request))
def _list_ctx(request):
    c=get_client(); return {**_ctx(request),'orders':c.list_orders(status=request.GET.get('status') or None,delivery_type=request.GET.get('delivery') or None,payment_type=request.GET.get('payment') or None,search=request.GET.get('q') or None,page=int_param(request,'page'))}
def table(request): return page(request,'orders/partials/table.html',_list_ctx(request))
def detail(request,order_id):
    o=required(get_client().get_order(order_id)); return page(request,'orders/detail.html',{**_ctx(request),'order':o,'flow':['PENDING','PAID','CONFIRMED','IN_PREPARATION','READY','DELIVERED']})
def change_status(request,order_id):
    if request.method!='POST': return HttpResponseBadRequest()
    get_client().update_order_status(order_id,request.POST.get('status','PENDING')); return redirect('order_detail',order_id=order_id)
def new_order(request):
    return page(request,'orders/new.html',{**_ctx(request),'clients':get_client().search_clients(''),'products':get_client().list_products(only_available=True,page_size=100).items,'coupons':get_client().list_coupons()})
def wizard_client_search(request):
    return page(request,'orders/partials/client_results.html',{**_ctx(request),'clients':get_client().search_clients(request.GET.get('q',''))})
def wizard_client_create(request):
    if request.method!='POST': return HttpResponseBadRequest()
    c=get_client().create_client(request.POST.get('name',''),request.POST.get('last_name',''),request.POST.get('phone','')); return HttpResponse(f'<div class="text-[13px] text-success font-medium">Cliente creado: {c.name} {c.lastName}</div>')
def wizard_product_search(request):
    c=get_client(); return page(request,'orders/partials/product_results.html',{**_ctx(request),'products':c.list_products(search=request.GET.get('q',''),only_available=True,page_size=100).items})
def wizard_cart(request):
    c=get_client(); rows=[]; subtotal=Decimal('0')
    for pid, qty in request.POST.items():
        if pid.startswith('qty_') and qty and int(qty)>0:
            p=c.get_product(pid[4:]); price=pricing.current_price(p)
            rows.append({'product':p,'qty':int(qty),'price':price,'subtotal':price*int(qty)}); subtotal+=price*int(qty)
    return page(request,'orders/partials/cart.html',{**_ctx(request),'rows':rows,'subtotal':subtotal})
def wizard_coupon(request):
    v=get_client().validate_coupon(request.POST.get('code',''),Decimal(request.POST.get('subtotal','0'))); return HttpResponse(f'<span class="text-[12px] {"text-success" if v.valid else "text-danger"}">{("Descuento: $ "+str(v.discount_amount)) if v.valid else v.reason}</span>')
def wizard_confirm(request):
    if request.method!='POST': return HttpResponseBadRequest()
    lines=[]
    for pid,qty in request.POST.items():
        if pid.startswith('qty_') and qty and int(qty)>0: lines.append({'product_id':pid[4:],'quantity':int(qty)})
    if not lines: return HttpResponseBadRequest('Agregá al menos un producto.')
    o=get_client().create_order({'client_id':request.POST.get('client_id') or None,'delivery_type':request.POST.get('delivery_type') or None,'payment_type':request.POST.get('payment_type') or None,'coupon_code':request.POST.get('coupon_code') or None,'lines':lines})
    return redirect('order_detail',order_id=o.id)
