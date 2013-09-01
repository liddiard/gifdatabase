from django.views.generic.base import TemplateView
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate
from search import engine
from gifdb.settings.base import S3_URL

class SearchForm(TemplateView):
    template_name = "front.html"

def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        render_to_response("Welcome to the cool kids club.")
    else:
        render_to_response("Whatcha think you're doin round these parts, son?")

def searchResults(request):
    query = request.GET['q']
    queryset = engine.query(query)
    return render_to_response('results.html', {'results': queryset, 'S3_URL': S3_URL})