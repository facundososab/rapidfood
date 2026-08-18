from .common import page,required
from ..services.factory import get_client

def _ctx(request): return {'active_section':'conversations'}
def index(request): return page(request,'conversations/index.html',{**_ctx(request),'conversations':get_client().list_conversations()})
def detail(request,conversation_id):
 c=get_client(); v=required(c.get_conversation(conversation_id)); return page(request,'conversations/detail.html',{**_ctx(request),'conversation':v})
