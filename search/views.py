from django.http import HttpResponseRedirect, HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth import (authenticate, login as django_login,
                                 logout as django_logout)
from django.template import RequestContext
from django.contrib.auth.forms import AuthenticationForm # currently unused
from django.utils.datastructures import MultiValueDictKeyError

from taggit.models import Tag

from search import engine
from gifdb.settings.base import S3_URL
from search.models import User, UserFavorite, Gif, TagInstance, UserScore, TagVote 

TAG_MAX_LENGTH = 32

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
    def safeVote(user, tag, up):
        try: # TODO: enforce m2m uniqueness on model validation as well
            tv = TagVote.objects.filter(user=user).get(tag=tag)
            tv.up = up
        except TagVote.DoesNotExist:
            tv = TagVote(user=user, tag=tag, up=up)
        finally:
            tv.save()
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                tag_id = request.POST['tag']
                set = request.POST['set']
            except KeyError:
                return HttpResponse("KeyError: necessary keys not found")
            try:
                tag = TagInstance.objects.get(pk=tag_id)
            except TagInstance.DoesNotExist:
                return HttpResponse("DoesNotExist: tag with id %s was not found"
                                    % tag_id)
            if user == tag.user_added:
                return HttpResponse("AccessError: user cannot vote on a tag "
                                    "they created themself")
            set = int(set)
            if set > 0:
                safeVote(user, tag, True)
            elif set < 0:
                safeVote(user, tag, False)
            else:
                try:
                    tv = TagVote.objects.filter(user=user).get(tag=tag)
                    tv.delete()
                except TagVote.DoesNotExist:
                    return HttpResponse("DoesNotExist: could not unset TagVote "
                                        "because TagVote doesn't exist")
            return HttpResponse("user: %s | tag id: %s | tag name: %s | set: %s" % (request.user, tag.pk, tag.tag, set))
        else:
            return HttpResponse("AuthenticationError: user is not authenticated")
    else:
        raise Http404

def ajaxGetTagVote(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                tag_id = request.POST['tag']
            except KeyError:
                return HttpResponse("KeyError: necessary keys not found")
            try:
                tv = TagVote.objects.filter(user=user).get(tag=tag_id)
            except TagVote.DoesNotExist:
                return HttpResponse("%s|0" % tag_id)
            if tv.up:
                return HttpResponse("%s|1" % tag_id)
            else:
                return HttpResponse("%s|-1" % tag_id)
        else:
            return HttpResponse("AuthenticationError: user is not authenticated")
    else:
        raise Http404

def ajaxAddTag(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                gif_id = request.POST['gif']
                tag_name = request.POST['tag']
            except KeyError:
                return HttpResponse("KeyError: necessary keys not found")
            if len(tag_name) > TAG_MAX_LENGTH:
                return HttpResponse("ValidationError: tag length is greater "
                                    "than max allowed length of %s chars" %
                                    TAG_MAX_LENGTH)
            try:
                gif = Gif.objects.get(pk=gif_id)
            except Gif.DoesNotExist:
                return HttpResponse("DoesNotExist: could not add tag to gif "
                                    "because gif matching id doesn't exist")
            t = Tag.objects.get_or_create(name=tag_name)[0]
            ti = TagInstance.objects.get_or_create(tag=t, content_object=gif, user_added=user)[0]
            return HttpResponse("ok|%s" % ti.pk)
        else:
            return HttpResponse("AuthenticationError: user is not authenticated")
    else:
        raise Http404

def ajaxEraseTag(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                tag_id = request.POST['tag']
            except KeyError:
                return HttpResponse("KeyError: necessary keys not found")
            try:
                ti = TagInstance.objects.get(pk=tag_id)
            except TagInstance.DoesNotExist:
                return HttpResponse("DoesNotExist: could not delete tag "
                                    "because tag matching id doesn't exist")
            if ti.user_added == user:
                ti.delete()
                return HttpResponse("Deleted tag")
            else:
                return HttpResponse("AccessError: the requesting user does "
                                    "not have permission to delete this tag")
        else:
            return HttpResponse("AuthenticationError: user is not authenticated")
    else:
        raise Http404
