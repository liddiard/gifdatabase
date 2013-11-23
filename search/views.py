import json, re
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect, HttpResponse
from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth import (authenticate, login as django_login,
                                 logout as django_logout)
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic.base import TemplateView

from taggit.models import Tag

from gifdb.settings.base import S3_URL
from search import engine
from search.models import TAG_MAX_LEN, User, UserFavorite, Gif, TagInstance, UserScore, TagVote 
from search.image import imgFromUrl, isAnimated


# page utility functions

def makeGroup(queryset, group):
    for obj in queryset:
        obj.group = group
    return queryset


# pages

class BasePageView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(BasePageView, self).get_context_data(**kwargs)
        context['S3_URL'] = S3_URL
        context['TAG_MAX_LEN'] = TAG_MAX_LEN
        context['recent_gifs'] = makeGroup(Gif.objects.order_by('-date_added')[:9], "recent")
        # context['recommended_gifs'] = makeGroup(Gif.objects.filter(date_added__gt=datetime.now()+timedelta(days=1)).order_by('-stars')[:9], "recommended")
        return context


class FrontPageView(TemplateView):

    template_name = "front.html"

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)
        context['S3_URL'] = S3_URL
        return context


class SearchResultsView(BasePageView):

    template_name = "results.html"

    def getResults(self, request):
        query = request.GET.get('q')
        results = engine.query(query)
        for result in results:
            result.gif.group = "results"
        return results

    def dispatch(self, request, *args, **kwargs):
        if not request.GET.get('q'):
            return redirect('front')
        return super(SearchResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SearchResultsView, self).get_context_data(**kwargs)
        context['results'] = self.getResults(self.request)
        return context


class ProfileView(BasePageView):
    
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        user_profile = get_object_or_404(User, username=self.kwargs\
                                                            .get('username'))
        context['username'] = user_profile
        print user_profile
        context['score'] = UserScore.objects.get(user=user_profile).score
        starred = UserFavorite.objects.filter(user=user_profile)
        context['starred_total'] = starred.count()
        context['starred_recent'] = makeGroup(starred
                                              .order_by('-date_favorited')[:8],
                                              "starred")
        added = Gif.objects.filter(user_added=user_profile)
        context['added_total'] = added.count()
        context['added_recent'] = makeGroup(added.order_by('-date_added')[:8],
                                            "added")
        return context


class ProfileStarredView(BasePageView):

    template_name = "profile_starred.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileStarredView, self).get_context_data(**kwargs)
        user_profile = get_object_or_404(User, username=self.kwargs\
                                                   .get('username'))
        context['username'] = user_profile
        starred = makeGroup(UserFavorite.objects.filter(user=user_profile)\
                            .order_by('-date_favorited'), "starred")
        context['starred'] = starred
        context['starred_total'] = starred.count()
        return context


class ProfileAddedView(BasePageView):

    template_name = "profile_added.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileAddedView, self).get_context_data(**kwargs)
        user_profile = get_object_or_404(User, username=self.kwargs\
                                                   .get('username'))
        context['username'] = user_profile
        added = Gif.objects.filter(user_added=user_profile)\
                                    .order_by('-date_added')
        context['added'] = added
        context['added_total'] = added.count()
        return context


# state management

def login(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
    except MultiValueDictKeyError:
        return redirect('front')
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
        return redirect('front')


# ajax api convenience functions

def jsonResponse(**kwargs):
    return HttpResponse(json.dumps(kwargs), content_type="application/json")

def error(error_type, message):
    return jsonResponse(result=1, error=error_type, message=message)

def authenticationError():
    return error("AuthenticationError", "User is not authenticated.")

def accessError(message):
    return error("AccessError", message)

def keyError(message):
    return error("KeyError", message)

def doesNotExist(message):
    return error("DoesNotExist", message)

def validationError(message):
    return error("ValidationError", message)


# ajax api

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
                return keyError("Required keys (tag, set) not found in request.")
            try:
                tag = TagInstance.objects.get(pk=tag_id)
            except TagInstance.DoesNotExist:
                return doesNotExist("Tag with id %s was not found." % tag_id)
            if user == tag.user_added:
                return accessError("User cannot vote on a tag they created "
                                   "themself.")
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
                    return doesNotExist("Could not unset TagVote because "
                                        "TagVote doesn't exist.")
            return jsonResponse(result=0, tag_id=tag.pk, tag_name=tag.tag.name,
                                set=set)
        else:
            return authenticationError()
    else:
        raise Http404

def ajaxGetTagVote(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                tag_id = request.POST['tag']
            except KeyError:
                return keyError("Required key (tag) not found in request.")
            try:
                tv = TagVote.objects.filter(user=user).get(tag=tag_id)
            except TagVote.DoesNotExist:
                return jsonResponse(result=0, tag=tag_id, vote=0)
            if tv.up:
                return jsonResponse(result=0, tag=tag_id, vote=1)
            else:
                return jsonResponse(result=0, tag=tag_id, vote=-1)
        else:
            return authenticationError()
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
                return keyError("Required keys (gif, tag) not found in request.")
            pattern = re.compile("^[a-zA-Z0-9\. '-]+$")
            if not pattern.match(tag_name):
                return validationError("Tag contains invalid characters.")
            if len(tag_name) > TAG_MAX_LEN:
                return validationError("Tag length is greater than max allowed "
                                       "length of %s chars." % TAG_MAX_LEN)
            try:
                gif = Gif.objects.get(pk=gif_id)
            except Gif.DoesNotExist:
                return doesNotExist("Could not add tag to gif because gif "
                                    "matching id %s doesn't exist." % gif_id)
            if gif.tags.count() > 11:
                return accessError("The gif associated with this tag already "
                                   "has the maximum number of tags.")
            t = Tag.objects.get_or_create(name=tag_name)[0]
            ti, created = TagInstance.objects.get_or_create(tag=t,
                                                         content_object=gif)
            if created:
                ti.user_added = user
                ti.save()
            else:
                pass
            return jsonResponse(result=0, taginstance=ti.pk)
        else:
            return authenticationError()
    else:
        raise Http404

def ajaxEraseTag(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                tag_id = request.POST['tag']
            except KeyError:
                return keyError("Required key (tag) not found in request.")
            try:
                ti = TagInstance.objects.get(pk=tag_id)
            except TagInstance.DoesNotExist:
                return doesNotExist("Could not delete tag because tag matching "
                                    "id %s doesn't exist." % tag_id)
            if ti.hasBeenVotedOn():
                return accessError("This tag has already been voted on and "
                                   "thus cannot be user-erased.")
            if ti.content_object.tags.count() < 5:
                return accessError("The gif associated with this tag has the "
                                   "already has the minimum number of tags.")
            else:
                if ti.user_added == user:
                    ti.delete()
                    return jsonResponse(result=0, message="Deleted tag.")
                else:
                    return accessError("The requesting user does not have "
                                       "permission to delete this tag.")
        else:
            return authenticationError()
    else:
        raise Http404

def ajaxGetStar(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                gif_id = request.POST['gif']
            except KeyError:
                return keyError("Required key (gif) not found in request.")
            try:
                gif = Gif.objects.get(pk=gif_id)
            except Gif.DoesNotExist:
                return doesNotExist("Could not get UserFavorite because Gif "
                                    "matching id %s does not exist." % gif_id)
            try:
                UserFavorite.objects.get(user=user, gif=gif)
                return jsonResponse(result=0, star=1)
            except UserFavorite.DoesNotExist:
                return jsonResponse(result=0, star=0)    
        else:
            return authenticationError()
    else:
        return Http404

def ajaxAddStar(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                gif_id = request.POST['gif']
            except KeyError:
                return keyError("Required key (gif) not found in request.")
            try:
                gif = Gif.objects.get(pk=gif_id)
            except Gif.DoesNotExist:
                return doesNotExist("Could not create UserFavorite because "
                                    "Gif matching id %s does not exist." % gif_id)
            uf = UserFavorite.objects.get_or_create(user=user, gif=gif)[0]
            return jsonResponse(result=0, userfavorite=uf.pk)
        else:
            return authenticationError()
    else:
        return Http404

def ajaxRemoveStar(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                gif_id = request.POST['gif']
            except KeyError:
                return keyError("Required key (gif) not found in request.")
            try:
                uf = UserFavorite.objects.get(user=user, gif=gif_id)
            except Gif.DoesNotExist:
                return doesNotExist("Could not create UserFavorite because "
                                    "Gif matching id %s does not exist." % gif_id)
            if uf.user == user:
                uf.delete()
                return jsonResponse(result=0, message="Deleted UserFavorite.")
            else:
                return accessError("The requesting user does not match the "
                                   "user who created the UserFavorite.")
        else:
            return authenticationError()
    else:
        return Http404

def ajaxCheckValidGif(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                filename = request.POST['filename']
            except KeyError:
                return keyError("Required key (filename) not found in request.")
            try:
                gif = Gif.objects.get(filename=filename)
                return error("AlreadyExistsError", "Gif %s already exists" %\
                             filename)
            except Gif.DoesNotExist:
                url = "http://i.imgur.com/%s.gif" % filename
                if isAnimated(imgFromUrl(url)):
                    return jsonResponse(result=0, url=url)
                else:
                    return error("InvalidFileError", "Image %s is not an "
                                 "animated gif." % filename)
        else:
            return authenticationError()
    else:
        return Http404

def ajaxAddGif(request):
    if request.is_ajax():
        if request.user.is_authenticated():
            user = request.user
            try:
                filename = request.POST['filename']
                tags = request.POST.getlist('tags[]')
            except KeyError:
                return keyError("Required keys (filename, tags) not found in "
                                "request.")
            try:
                gif = Gif.objects.get(filename=filename)
                return error("AlreadyExistsError", "Gif %s already exists" %\
                             filename)
            except Gif.DoesNotExist:
                pattern = re.compile("^[a-zA-Z0-9\. '-]+$")
                valid_tags = [tag_name for tag_name in tags if 
                              pattern.match(tag_name) and
                              len(tag_name) < TAG_MAX_LEN]
                if len(valid_tags) < 4:
                    return validationError("Only %s of the tags were valid. "
                                           "4 are required." % len(valid_tags))
                url = "http://i.imgur.com/%s.gif" % filename
                if isAnimated(imgFromUrl(url)):
                    gif = Gif(filename=filename, user_added=user)
                    gif.save()
                    for tag_name in valid_tags:
                        t = Tag.objects.get_or_create(name=tag_name)[0]
                        ti, created = TagInstance.objects.get_or_create(tag=t,
                                                                     content_object=gif)
                        if created:
                            ti.user_added = user
                            ti.save()
                        else:
                            pass
                    return jsonResponse(result=0, gif=gif.pk)
                else:
                    return error("InvalidFileError", "Image %s is not an "
                                 "animated gif." % filename)
        else:
            return authenticationError()
    else:
        return Http404

# TODO: currently unused
def authenticatedAjax(func, request):
    if request.is_ajax():
        if request.user.is_authenticated():
            return func(request)
        else:
            return authenticationError()
    else:
        return Http404

# TODO: currently unused
def ajaxGetStarView(request):
    return authenticatedAjax(ajaxGetStar, request)
