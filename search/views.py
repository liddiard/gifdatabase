from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth import (authenticate, login as django_login,
                                 logout as django_logout)
from django.template import RequestContext
from django.contrib.auth.forms import AuthenticationForm
from search import engine
from gifdb.settings.base import S3_URL
from search.models import User, UserFavorite

def frontPage(request):
    return render_to_response('front.html', {'S3_URL': S3_URL},
                              context_instance=RequestContext(request))

def searchResults(request):
    query = request.GET['q']
    queryset = engine.query(query)
    return render_to_response('results.html',
                              {'results': queryset, 'S3_URL': S3_URL},
                              context_instance=RequestContext(request))

def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            django_login(request, user)
            return redirect('main')
        else:
            return render_to_response("Disabled account.")
    else:
        return render_to_response("Your login is bad and you should feel bad.")

def logout(request):
    django_logout(request)
    return redirect('main')

def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    starred_recent = UserFavorite.objects.filter(user=user_profile)\
                                                 .order_by('-date_favorited')[:5]
    added_recent = None
    tagged_recent = None
    
    return render_to_response('profile.html',
                              {'username': user_profile, 
                               'starred_recent': starred_recent,'S3_URL': S3_URL},
                              context_instance=RequestContext(request))

def profileStarred(request, username):
    pass