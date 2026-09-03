from decimal import Decimal
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from .common import page, required, int_param
from ..services.factory import get_client
from ..services import dtos
from ..services.client import Page
from ..domain import pricing

LIST_PAGE_SIZE = 12
# UI-only filter groups over the real OrderStatus enum (backend rules unchanged).
ORDER_FILTER_GROUPS = {
    "": None,
    "proceso": {"PENDING", "PAID", "CONFIRMED", "IN_PREPARATION", "READY"},
    "completados": {"DELIVERED", "PICKED_UP"},
    "cancelados": {"CANCELLED"},
}
STATUS_FILTER_TABS = [
    ("", "Todos"),
    ("proceso", "En proceso"),
    ("completados", "Completados"),
    ("cancelados", "Cancelados"),
]
# Mirrors the backend CancelOrderUseCase cancellable states.
CANCELLABLE_STATUSES = {"DRAFT", "PENDING", "PAID"}

def _ctx(request):
    c=get_client(); return {'active_section':'orders','statuses':dtos.ORDER_STATUS_LABELS,'delivery_types':dtos.DELIVERY_TYPE_LABELS,'payment_types':dtos.PAYMENT_TYPE_LABELS,'client':c}
def index(request):
    c=get_client()
    products=[]
    for p in c.list_products(only_available=False, page_size=200).items:
        price=pricing.current_price(p)
        if price is None:
            full=c.get_product(p.id)
            price=pricing.current_price(full) if full else None
        products.append({'id':p.id,'name':p.name,'description':p.description,'available':p.available,'imageUrl':p.imageUrl,'categoryId':p.categoryId,'category':p.category.description if p.category else '','price':price})
    return page(request,'orders/index.html',{**_ctx(request),'recent_orders':c.list_orders(page_size=16).items,'categories':c.list_categories(),'products':products,'client_options':[{'id':x.id,'name':x.name,'lastName':x.lastName,'phoneNumber':x.phoneNumber} for x in c.search_clients('')],'shipping_cost':c.get_business_config().shippingCost})
def _list_ctx(request):
    c=get_client(); return {**_ctx(request),'orders':c.list_orders(status=request.GET.get('status') or None,delivery_type=request.GET.get('delivery') or None,payment_type=request.GET.get('payment') or None,search=request.GET.get('q') or None,page=int_param(request,'page'))}
def table(request): return page(request,'orders/partials/table.html',_list_ctx(request))

_EMPTY_PAGE = Page(items=[], total=0, page=1, page_size=LIST_PAGE_SIZE)

def _listing_ctx(request):
    """Card-grid listing: UI filters, local search and pagination over the full set.

    The backend exposes a flat order list, so grouping (En proceso / Completados)
    and search happen here — presentation only, never touching backend rules.
    """
    c = get_client()
    filtro = request.GET.get("filtro", "") or ""
    search = (request.GET.get("q") or "").strip()
    page_no = int_param(request, "page")
    base = {**_ctx(request), "status_filters": STATUS_FILTER_TABS,
            "current_filter": filtro, "search": search,
            "cancellable_statuses": CANCELLABLE_STATUSES}
    try:
        rows = [o for o in c.list_orders(page=1, page_size=1000).items if o is not None]
    except Exception:
        return {**base, "orders": _EMPTY_PAGE, "load_error": True, "start_index": 0}
    group = ORDER_FILTER_GROUPS.get(filtro)
    if group is not None:
        rows = [o for o in rows if o.status in group]
    if search:
        needle = search.lower()
        def _match(o):
            if needle in o.id.lower():
                return True
            cli = o.client
            return bool(cli and (needle in (cli.name or "").lower()
                                 or needle in (cli.lastName or "").lower()
                                 or needle in (cli.phoneNumber or "").lower()))
        rows = [o for o in rows if _match(o)]
    rows.sort(key=lambda o: o.createdAt, reverse=True)
    products = {}
    try:
        products = {p.id: p for p in c.list_products(only_available=False, page_size=500).items}
    except Exception:
        products = {}
    for o in rows:
        for line in o.lines:
            if line.product is None and products:
                line.product = products.get(line.productId) or line.product
    total = len(rows)
    start = (page_no - 1) * LIST_PAGE_SIZE
    orders = Page(items=rows[start:start + LIST_PAGE_SIZE], total=total,
                  page=page_no, page_size=LIST_PAGE_SIZE)
    return {**base, "orders": orders, "start_index": start, "load_error": False}

def listing(request):
    return page(request, "orders/list.html", _listing_ctx(request))

def listing_grid(request):
    return render(request, "orders/partials/grid.html", _listing_ctx(request))

def cancel(request, order_id):
    if request.method != "POST":
        return HttpResponseBadRequest()
    get_client().cancel_order(order_id)
    return redirect("orders_listing")
def detail(request,order_id):
    o=required(get_client().get_order(order_id)); return page(request,'orders/detail.html',{**_ctx(request),'order':o,'flow':['PENDING','PAID','CONFIRMED','IN_PREPARATION','READY','DELIVERED']})
def change_status(request,order_id):
    if request.method!='POST': return HttpResponseBadRequest()
    get_client().update_order_status(order_id,request.POST.get('status','PENDING')); return redirect('order_detail',order_id=order_id)
def new_order(request):
    c=get_client()
    products=[]
    for p in c.list_products(only_available=True,page_size=200).items:
        price=pricing.current_price(p)
        if price is None:
            full=c.get_product(p.id)
            price=pricing.current_price(full) if full else None
        products.append({'id':p.id,'name':p.name,'category':p.category.description if p.category else '','price':price})
    return page(request,'orders/new.html',{**_ctx(request),'clients':c.search_clients(''),'products':products,'coupons':c.list_coupons()})
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
    payload={'client_id':request.POST.get('client_id') or None,'origin':'IN_PLACE','delivery_type':request.POST.get('delivery_type') or None,'payment_type':request.POST.get('payment_type') or None,'coupon_code':request.POST.get('coupon_code') or None,'lines':lines}
    if payload['delivery_type']=='DELIVERY' and request.POST.get('street'):
        c=get_client()
        try:
            addr=c.create_address({'street':request.POST.get('street'),'street_number':request.POST.get('street_number'),'floor':request.POST.get('floor'),'apartment':request.POST.get('apartment'),'city':request.POST.get('city'),'province':request.POST.get('province'),'postal_code':request.POST.get('postal_code')})
            payload['address_id']=addr.id
        except NotImplementedError:
            pass
    o=get_client().create_order(payload)
    return redirect('order_detail',order_id=o.id)
