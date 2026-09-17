from decimal import Decimal
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
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
        price = pricing.current_price(p)
        is_variable = pricing.has_variable_price(p)
        products.append({'id':p.id,'name':p.name,'description':p.description,'available':p.available,'imageUrl':p.imageUrl,'categoryId':p.categoryId,'category':p.category.description if p.category else '','price':price,'is_variable':is_variable})
    business = c.get_business_config()
    pos_config = {
        'minOrder': float(business.minOrder or 0),
        'productConfigUrl': reverse('orders_new_product_config', args=['0000']),
    }
    return page(request,'orders/index.html',{**_ctx(request),'recent_orders':c.list_orders(page_size=16).items,'categories':c.list_categories(),'products':products,'client_options':[{'id':x.id,'name':x.name,'lastName':x.lastName,'phoneNumber':x.phoneNumber} for x in c.search_clients('')],'pos_config':pos_config})
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
        products.append({'id':p.id,'name':p.name,'category':p.category.description if p.category else '','price':price})
    return page(request,'orders/new.html',{**_ctx(request),'clients':c.search_clients(''),'products':products,'coupons':c.list_coupons()})
def wizard_client_search(request):
    return page(request,'orders/partials/client_results.html',{**_ctx(request),'clients':get_client().search_clients(request.GET.get('q',''))})
def wizard_client_create(request):
    if request.method!='POST': return HttpResponseBadRequest()
    c=get_client().create_client(request.POST.get('name',''),request.POST.get('last_name',''),request.POST.get('phone','')); return HttpResponse(f'<div class="text-[13px] text-success font-medium">Cliente creado: {c.name} {c.lastName}</div>')
def orders_client_create(request):
    """Create a client from the POS (JSON so the Alpine modal can react)."""
    if request.method!='POST': return HttpResponseBadRequest()
    full=(request.POST.get('name') or '').strip()
    last=(request.POST.get('last_name') or '').strip()
    phone=(request.POST.get('phone') or '').strip()
    if full and not last:
        parts=full.split()
        full, last = parts[0], ' '.join(parts[1:])
    if not (full and phone):
        return JsonResponse({'ok':False,'error':'Completá nombre y teléfono.'})
    try:
        c=get_client().create_client(full, last, phone)
    except Exception as e:
        msg=str(e) or 'No se pudo crear el cliente.'
        if 'already exists' in msg.lower():
            msg='Ya existe un cliente con ese teléfono.'
        return JsonResponse({'ok':False,'error':msg})
    return JsonResponse({'ok':True,'client':{'id':c.id,'name':c.name,'lastName':c.lastName,'phoneNumber':c.phoneNumber}})
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
    import json
    lines = []
    cart_payload = request.POST.get('cart_payload')
    if cart_payload:
        lines = json.loads(cart_payload)
    if not lines: return HttpResponseBadRequest('Agregá al menos un producto.')
    client_id=request.POST.get('client_id') or None
    # Keep the typed/selected name as a snapshot even when a client is linked, so the
    # order still shows who it belonged to if the client is later deleted.
    client_name=(request.POST.get('client_name') or '').strip() or None
    payload={'client_id':client_id,'client_name':client_name,'origin':'IN_PLACE','delivery_type':request.POST.get('delivery_type') or None,'payment_type':request.POST.get('payment_type') or None,'coupon_code':(request.POST.get('coupon_code') or '').strip() or None,'lines':lines}
    for field in ('street','street_number','floor','apartment','city','province','postal_code'):
        value=(request.POST.get(field) or '').strip()
        if value: payload[field]=value
    if payload['delivery_type']=='DELIVERY' and request.POST.get('street'):
        c=get_client()
        try:
            addr=c.create_address({'street':request.POST.get('street'),'street_number':request.POST.get('street_number'),'floor':request.POST.get('floor'),'apartment':request.POST.get('apartment'),'city':request.POST.get('city'),'province':request.POST.get('province'),'postal_code':request.POST.get('postal_code')})
            payload['address_id']=addr.id
        except NotImplementedError:
            pass
    o=get_client().create_order(payload)
    return redirect('order_detail',order_id=o.id)


def wizard_validate_coupon(request):
    """Coupon discount preview for the POS (read-only)."""
    if request.method!='POST': return HttpResponseBadRequest()
    code=(request.POST.get('coupon_code') or '').strip()
    if not code: return JsonResponse({'valid':False,'reason':'','discount_amount':''})
    subtotal=Decimal(request.POST.get('subtotal') or '0')
    v=get_client().validate_coupon(code, subtotal)
    return JsonResponse({'valid':v.valid,'reason':v.reason,
                         'discount_amount':str(v.discount_amount or '')})


def wizard_quote(request):
    """Delivery quote proxy for the POS (server-side call to the backend)."""
    if request.method!='POST': return HttpResponseBadRequest()
    address={field:(request.POST.get(field) or '').strip() for field in
             ('street','street_number','floor','apartment','city','province','postal_code')}
    if not (address['street'] and address['street_number'] and address['city'] and address['province']):
        return JsonResponse({'available':False,'error':'Completá calle, número, ciudad y provincia.'})
    c=get_client()
    try:
        business=c.get_business_config()
        result=c.quote_delivery(business.id, address)
    except Exception as e:
        return JsonResponse({'available':False,'error':str(e) or 'No se pudo calcular el envío.'})
    return JsonResponse(result)


def product_config_modal(request, product_id):
    p = get_client().get_product(product_id)
    pc_config = {
        'productId': p.id,
        'productName': p.name,
        'variants': [
            {
                'id': v.id,
                'name': v.name,
                'price': float(v.currentPrice) if v.currentPrice is not None else 0,
                'available': bool(v.available),
                'ingredients': [
                    {'id': i.ingredientId, 'name': i.name, 'removable': bool(i.removable)}
                    for i in v.ingredients
                ],
            }
            for v in p.variants
        ],
        'modifierGroups': {
            g.id: {
                'name': g.name,
                'min': g.minSelections,
                'max': g.maxSelections,
                'options': [o.id for o in g.options],
            }
            for g in p.modifierGroups
        },
        'optionMeta': {
            o.id: {
                'name': o.name,
                'priceDelta': float(o.priceDelta) if o.priceDelta is not None else 0,
                'groupId': g.id,
            }
            for g in p.modifierGroups
            for o in g.options
        },
    }
    return page(request, 'orders/partials/product_config_modal.html', {'product': p, 'pc_config': pc_config})
