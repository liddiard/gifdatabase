from django.http import HttpResponseRedirect, HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth import (authenticate, login as django_login,
                                 logout as django_logout)
from django.template import RequestContext
from django.contrib.auth.forms import AuthenticationForm # currently unused
from django.utils.datastructures import MultiValueDictKeyError

from search import engine
from gifdb.settings.base import S3_URL
from search.models import User, UserFavorite, Gif, TagInstance, UserScore

def frontPage(request):
    return render_to_response('front.html', {'S3_URL': S3_URL},
                              context_instance=RequestContext(request))

def searchResults(request):
    query = request.GET['q']
    results = engine.query(query)
    return render_to_response('results.html',
                              {'results': results, 'S3_URL': S3_URL},
                              context_instance=RequestContext(request))

def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    user_score = UserScore.objects.get(user=user_profile).score
    starred_recent = UserFavorite.objects\
                                         .filter(user=user_profile)\
                                         .order_by('-date_favorited')[:5]
    added_recent = Gif.objects.filter(user_added=user_profile)\
                              .order_by('-date_added')[:5]
    tagged_recent = TagInstance.objects.filter(user_added=user_profile)\
                                       .order_by('date_added')[:5]
    
    template_vars = {'username': user_profile, 
                     'starred_recent': starred_recent,
                     'added_recent': added_recent,
                     'tagged_recent': tagged_recent,
                     'score': user_score,
                     'S3_URL': S3_URL}
    
    return render_to_response('profile.html', template_vars,
                              context_instance=RequestContext(request))

def profileStarred(request, username):
    pass

def login(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
    except MultiValueDictKeyError:
        return redirect('main')
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            django_login(request, user)
            return redirect(request.META['HTTP_REFERER'])
        else:
            return render_to_response("Disabled account.")
    else:
        return render_to_response("Your login is bad and you should feel bad.")

def logout(request):
    django_logout(request)
    try:
        return redirect(request.META['HTTP_REFERER'])
    except KeyError:
        return redirect('main')

def ajaxTagVote(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            try:
                tag_id = request.POST['tag']
                set = request.POST['set']
            except KeyError:
                return HttpResponse("KeyError: necessary keys not found") # incorrect post
            try:
                tag = TagInstance.objects.get(pk=tag_id)
            except TagInstance.DoesNotExist:
                return HttpResponse("DoesNotExist: tag id %s was not found" % tag_id)
            return HttpResponse("user: %s | tag id: %s | tag name: %s | set: %s" % (request.user, tag.pk, tag.tag, set))
        else:
            return HttpResponse("AuthenticationError: user is not authenticated")
    else:
        raise Http404
