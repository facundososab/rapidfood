from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from .common import page,required,int_param
from ..services.factory import get_client
from ..domain.clients import client_metrics

def _ctx(request): return {'active_section':'clients'}
def _list(request):
 c=get_client(); rows=c.list_clients(search=request.GET.get('q') or None,page=int_param(request,'page')); return {**_ctx(request),'clients':rows,'orders':c.all_orders(),'conversations':c.list_conversations()}
def index(request): return page(request,'clients/index.html',_list(request))
def table(request): return page(request,'clients/partials/table.html',_list(request))
def detail(request,client_id):
 c=get_client(); cli=required(c.get_client(client_id)); orders=[o for o in c.all_orders() if o.clientId==client_id]; conv=[v for v in c.list_conversations() if v.clientId==client_id]; return page(request,'clients/detail.html',{**_ctx(request),'client_obj':cli,'orders':orders,'conversations':conv,'metrics':client_metrics(client_id,c.all_orders(),c.list_conversations())})
def delete(request,client_id):
 if request.method!='POST': return HttpResponseBadRequest()
 try:
  get_client().delete_client(client_id)
 except Exception as e:
  return page(request,'clients/index.html',{**_list(request),'error':f'No se pudo eliminar el cliente: {e}'})
 return redirect('clients')
