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
 p=required(get_client().get_product(product_id)); return page(request,'products/detail.html',{**_ctx(request),'product':p,'current_price':pricing.current_price(p),'history':pricing.price_history(p)})
def form(request,product_id=None):
 product=get_client().get_product(product_id) if product_id else None; return page(request,'products/form.html',{**_ctx(request),'product':product,'current_price':pricing.current_price(product) if product else None})
def save(request,product_id=None):
 if request.method!='POST': return HttpResponseBadRequest()
 p=get_client().save_product({'id':product_id,'name':request.POST['name'],'description':request.POST['description'],'image_url':request.POST.get('image_url') or None,'category_id':request.POST['category_id'],'available':request.POST.get('available')=='on','price':request.POST.get('price') or None}); return redirect('product_detail',product_id=p.id)
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
