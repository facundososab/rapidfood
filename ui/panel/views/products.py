from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page,required,int_param
from ..services.factory import get_client
from ..domain import pricing

def _ctx(request): return {'active_section':'products','categories':get_client().list_categories()}
def _list(request):
 c=get_client(); return {**_ctx(request),'products':c.list_products(search=request.GET.get('q') or None,category_id=request.GET.get('category') or None,page=int_param(request,'page'))}
def index(request): return page(request,'products/index.html',_list(request))
def table(request): return page(request,'products/partials/table.html',_list(request))
def detail(request,product_id):
 p=required(get_client().get_product(product_id)); return page(request,'products/detail.html',{**_ctx(request),'product':p,'current_price':pricing.current_price(p),'history':pricing.price_history(p),'ingredients_list':get_client().list_ingredients()})
def form(request,product_id=None):
 product=get_client().get_product(product_id) if product_id else None; return page(request,'products/form.html',{**_ctx(request),'product':product,'current_price':pricing.current_price(product) if product else None})
def save(request, product_id=None):
    if request.method != 'POST': return HttpResponseBadRequest()
    
    payload = {
        'id': product_id,
        'name': request.POST['name'],
        'description': request.POST['description'],
        'image_url': request.POST.get('image_url') or None,
        'category_id': request.POST['category_id'],
    }
    # Availability has its own control; only touch it when the form provides it.
    if 'available' in request.POST:
        payload['available'] = request.POST.get('available') == 'on'

    client = get_client()

    if product_id:
        p = client.save_product(payload)
        messages.success(request, 'Producto actualizado.')
        return redirect('product_detail', product_id=p.id)
    
    # New product creation
    p = client.save_product(payload)
    product = required(client.get_product(p.id))
    default_variant = product.variants[0] if product and getattr(product, 'variants', None) else None
    
    has_variants = request.POST.get('has_variants') == 'true'
    
    if not has_variants:
        price = request.POST.get('single_price')
        if default_variant and price:
            client.set_variant_price(default_variant.id, price)
    else:
        names = request.POST.getlist('variant_names[]')
        prices = request.POST.getlist('variant_prices[]')
        
        if names and prices and default_variant:
            # Update default variant to first variant
            client.update_variant(default_variant.id, {"name": names[0]})
            client.set_variant_price(default_variant.id, prices[0])
            
            # Create the rest
            for i in range(1, len(names)):
                if i < len(prices) and names[i].strip() and prices[i].strip():
                    client.create_variant(p.id, {
                        "name": names[i],
                        "initial_price": prices[i]
                    })

    return redirect('product_detail', product_id=p.id)

def toggle_availability(request,product_id):
 p=required(get_client().get_product(product_id)); get_client().set_product_availability(product_id,not p.available); return redirect('product_detail',product_id=product_id)
def delete(request,product_id):
 if request.method!='POST': return HttpResponseBadRequest()
 try:
  get_client().delete_product(product_id)
 except Exception as e:
  messages.error(request, f'No se pudo eliminar el producto: {e}')
  return redirect('products')
 messages.success(request, 'Producto eliminado.')
 return redirect('products')
def add_price(request,product_id):
 if request.method!='POST': return HttpResponseBadRequest()
 get_client().add_product_price(product_id,Decimal(request.POST['price'])); return redirect('product_detail',product_id=product_id)
def categories(request): return page(request,'products/categories.html',_ctx(request))
def save_category(request):
 if request.method!='POST': return HttpResponseBadRequest()
 get_client().save_category({'description':request.POST['description']}); return redirect('categories')


def variant_price_save(request, variant_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    back = request.META.get('HTTP_REFERER', 'products')
    try:
        price = Decimal(request.POST['price'])
    except (KeyError, InvalidOperation):
        messages.error(request, 'Ingresá un precio válido.')
        return redirect(back)
    since_date = None
    raw_date = (request.POST.get('since_date') or '').strip()
    if raw_date:
        try:
            since_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'La fecha ingresada no es válida.')
            return redirect(back)
    get_client().set_variant_price(variant_id, price, since_date)
    messages.success(request, 'Precio actualizado.')
    return redirect(back)


def variant_save(request, product_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().create_variant(product_id, {
        "name": request.POST["name"],
        "initial_price": request.POST["initial_price"]
    })
    return redirect('product_detail', product_id=product_id)

def modifier_group_save(request, product_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().create_modifier_group(product_id, {
        "name": request.POST["name"],
        "min_selections": int(request.POST.get("min_selections", 0)),
        "max_selections": int(request.POST.get("max_selections", 1))
    })
    return redirect('product_detail', product_id=product_id)

def modifier_group_update(request, group_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    payload = {"min_selections": 1 if request.POST.get("min_selections") else 0}
    if request.POST.get("name"):
        payload["name"] = request.POST["name"]
    if request.POST.get("max_selections"):
        payload["max_selections"] = int(request.POST["max_selections"])
    get_client().update_modifier_group(group_id, payload)
    messages.success(request, 'Grupo actualizado.')
    return redirect(request.META.get('HTTP_REFERER', 'products'))

def modifier_group_delete(request, group_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().delete_modifier_group(group_id)
    messages.success(request, 'Grupo eliminado.')
    return redirect(request.META.get('HTTP_REFERER', 'products'))

def modifier_option_save(request, group_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().create_modifier_option(group_id, {
        "name": request.POST["name"],
        "price_delta": request.POST["price_delta"]
    })
    messages.success(request, 'Opción agregada.')
    return redirect(request.META.get('HTTP_REFERER', 'products'))

def modifier_option_delete(request, option_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().delete_modifier_option(option_id)
    messages.success(request, 'Opción eliminada.')
    return redirect(request.META.get('HTTP_REFERER', 'products'))


def variant_ingredients_save(request, variant_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    
    # Checkboxes come as ingredient_ids list
    ingredient_ids = request.POST.getlist('ingredients')
    removable_ids = request.POST.getlist('removable') # which ones are removable
    
    payload = []
    for ing_id in ingredient_ids:
        payload.append({
            "ingredient_id": ing_id,
            "removable": ing_id in removable_ids
        })
        
    get_client().set_variant_ingredients(variant_id, {"entries": payload})
    return redirect(request.META.get('HTTP_REFERER', 'products'))


def ingredient_save(request):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().create_ingredient({"name": request.POST["name"]})
    return redirect(request.META.get('HTTP_REFERER', 'products'))
