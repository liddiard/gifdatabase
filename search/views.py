from django.views.generic.base import TemplateView
from django.shortcuts import render_to_response
from search import engine
from gifdb.settings.base import S3_URL

class SearchForm(TemplateView):
    template_name = "front.html"

def SearchResults(request):
    query = request.GET['q']
    queryset = engine.query(query)
    return render_to_response('results.html', {'results': queryset, 'S3_URL': S3_URL})