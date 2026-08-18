from .common import page,required,int_param
from ..services.factory import get_client
from ..services import dtos

def _ctx(request): return {'active_section':'payments','statuses':dtos.PAYMENT_STATUS_LABELS}
def _list(request):
 return {**_ctx(request),'payments':get_client().list_payments(status=request.GET.get('status') or None,provider=request.GET.get('provider') or None,page=int_param(request,'page'))}
def index(request): return page(request,'payments/index.html',_list(request))
def table(request): return page(request,'payments/partials/table.html',_list(request))
def detail(request,payment_id):
 c=get_client(); p=required(c.get_payment(payment_id)); return page(request,'payments/detail.html',{**_ctx(request),'payment':p,'order':c.get_order(p.orderId)})
