from decimal import Decimal
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
        'available': request.POST.get('available') == 'on'
    }
    
    client = get_client()
    
    if product_id:
        p = client.save_product(payload)
        return redirect('product_detail', product_id=p.id)
    
    # New product creation
    p = client.save_product(payload)
    product = client.get_product(p.id)
    default_variant = product.variants[0] if product.variants else None
    
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
 p=get_client().get_product(product_id); get_client().set_product_availability(product_id,not p.available); return redirect('product_detail',product_id=product_id)
def delete(request,product_id):
 if request.method!='POST': return HttpResponseBadRequest()
 try:
  get_client().delete_product(product_id)
 except Exception as e:
  return page(request,'products/index.html',{**_list(request),'error':f'No se pudo eliminar el producto: {e}'})
 return redirect('products')
def add_price(request,product_id):
 if request.method!='POST': return HttpResponseBadRequest()
 get_client().add_product_price(product_id,Decimal(request.POST['price'])); return redirect('product_detail',product_id=product_id)
def categories(request): return page(request,'products/categories.html',_ctx(request))
def save_category(request):
 if request.method!='POST': return HttpResponseBadRequest()
 get_client().save_category({'description':request.POST['description']}); return redirect('categories')


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

def modifier_option_save(request, group_id):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().create_modifier_option(group_id, {
        "name": request.POST["name"],
        "price_delta": request.POST["price_delta"]
    })
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
        
    get_client().set_variant_ingredients(variant_id, payload)
    return redirect(request.META.get('HTTP_REFERER', 'products'))


def ingredient_save(request):
    if request.method != 'POST': return HttpResponseBadRequest()
    get_client().create_ingredient({"name": request.POST["name"]})
    return redirect(request.META.get('HTTP_REFERER', 'products'))
