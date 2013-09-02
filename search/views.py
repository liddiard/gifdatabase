from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.core.context_processors import csrf
from search import engine
from gifdb.settings.base import S3_URL

def frontPage(request):
    return render_to_response('front.html', context_instance=RequestContext(request))

def doLogin(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return render_to_response("Logged in!")
        else:
            return render_to_response("Disabled account.")
    else:
        return render_to_response("Whatcha think you're doin round these parts, son?")

def searchResults(request):
    query = request.GET['q']
    queryset = engine.query(query)
    return render_to_response('results.html', {'results': queryset, 'S3_URL': S3_URL})