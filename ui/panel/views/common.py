from django.http import Http404
from django.shortcuts import render

def page(request, template, context, partial=None):
    context.setdefault('active_section', '')
    return render(request, partial if request.headers.get('HX-Request') and partial else template, context)

def required(value):
    if value is None:
        raise Http404
    return value

def int_param(request, key, default=1):
    try: return max(1, int(request.GET.get(key, default)))
    except ValueError: return default
