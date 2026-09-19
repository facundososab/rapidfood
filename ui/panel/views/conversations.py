from django.http import HttpResponseBadRequest

from .common import page, required
from ..services.factory import get_client


_PANE_PARTIAL = 'conversations/partials/conversation.html'


def _label(conversation) -> str:
    if conversation is not None and conversation.clientName:
        return conversation.clientName
    return 'Cliente sin identificar'


def _ctx(request, conversations, conversation):
    return {
        'active_section': 'conversations',
        'conversations': conversations,
        'conversation': conversation,
        'label': _label(conversation),
        'unassigned_count': sum(1 for c in conversations if not c.clientId),
    }


def _pane(request, conversation, conversations, error=None):
    context = _ctx(request, conversations, conversation)
    context['error'] = error
    return page(request, 'conversations/detail.html', context, partial=_PANE_PARTIAL)


def index(request):
    conversations = get_client().list_conversations()
    conversation = (
        get_client().get_conversation(conversations[0].id) if conversations else None
    )
    return page(
        request,
        'conversations/index.html',
        _ctx(request, conversations, conversation),
    )


def detail(request, conversation_id):
    conversations = get_client().list_conversations()
    conversation = required(get_client().get_conversation(conversation_id))
    return _pane(request, conversation, conversations)


def client_message(request, conversation_id):
    """The operator types as the customer; the agent answers."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    conversations = get_client().list_conversations()
    content = (request.POST.get('content') or '').strip()
    if not content:
        return _pane(
            request, required(get_client().get_conversation(conversation_id)), conversations
        )
    try:
        conversation = get_client().send_client_message(conversation_id, content)
    except RuntimeError as exc:
        return _pane(
            request,
            required(get_client().get_conversation(conversation_id)),
            conversations,
            error=str(exc) or 'No se pudo obtener respuesta del agente.',
        )
    return _pane(request, required(conversation), conversations)


def operator_message(request, conversation_id):
    """A human writes in the conversation (the agent stays quiet)."""
    if request.method != 'POST':
        return HttpResponseBadRequest()
    conversations = get_client().list_conversations()
    content = (request.POST.get('content') or '').strip()
    if content:
        get_client().send_operator_message(conversation_id, content)
    return _pane(
        request, required(get_client().get_conversation(conversation_id)), conversations
    )


def takeover(request, conversation_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    conversations = get_client().list_conversations()
    conversation = get_client().set_conversation_takeover(conversation_id, True)
    return _pane(request, required(conversation), conversations)


def release(request, conversation_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    conversations = get_client().list_conversations()
    conversation = get_client().set_conversation_takeover(conversation_id, False)
    return _pane(request, required(conversation), conversations)
