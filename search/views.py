from django.views.generic import View, ListView
from django.views.generic.base import TemplateView
from django.http import HttpRequest
from django.shortcuts import render_to_response
from search.models import Gif
from search import engine

class SearchForm(TemplateView):
    template_name = "index.html"

def SearchResults(request):
    query = request.GET['q']
    queryset = engine.query(query)
    return render_to_response('results.html', {'results': queryset})