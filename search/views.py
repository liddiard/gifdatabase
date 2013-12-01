import json, re
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import (authenticate, login as django_login,
                                 logout as django_logout)
from django.contrib.auth import views as auth_views
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse

from taggit.models import Tag
from registration.backends.default.views import (ActivationView as
                                                 BaseActivationView,
                                                 RegistrationView as
                                                 BaseRegistrationView)

from search import engine
from search.models import (TAG_MAX_LEN, User, UserFavorite, Gif, TagInstance, 
                           UserScore, TagVote)
from search.image import imgFromUrl, isAnimated


# page utility functions

def group(queryset, group, intermediate=False):
    if intermediate:
        for obj in queryset:
            obj.gif.group = group
    else:
        for obj in queryset:
            obj.group = group
    return queryset

def paginate(request, queryset):
    paginator = Paginator(queryset, 19)
    page = request.GET.get('page')
    try:
        qp = paginator.page(page)
    except PageNotAnInteger:
        qp = paginator.page(1)
    except EmptyPage:
        qp = paginator.page(paginator.num_pages)
    return qp


# pages

## inheritable

class BasePageView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(BasePageView, self).get_context_data(**kwargs)
        user = self.request.user
        context['TAG_MAX_LEN'] = TAG_MAX_LEN
        context['recent_gifs'] = group(Gif.objects\
                                       .order_by('-date_added')[:9], "recent")
        if user.is_authenticated(): # get gifs similar to the ones on which
                                    # user has added tags
            spots = 9
            recommended_gifs = []
            user_added_tags = TagInstance.objects.filter(user_added=user)\
                                                        .order_by('?')[:4]
            for tag in user_added_tags:
                remaining = spots - len(recommended_gifs)
                recommended_gifs += group(tag.content_object.tags\
                                          .similar_objects()[:remaining],
                                          "recommended")
                if len(recommended_gifs) == spots:
                    break # stop looping if all spots are filled
        else: # get the most starred gifs added within the last week
            recommended_gifs = group(Gif.objects\
                                     .filter(date_added__gt=datetime.now()-
                                     timedelta(days=7)).order_by('-stars')[:9],
                                     "recommended")
        context['recommended_gifs'] = recommended_gifs 
        return context


## core application

class FrontPageView(TemplateView):

    template_name = "front.html"

    def get_context_data(self, **kwargs):
        context = super(FrontPageView, self).get_context_data(**kwargs)
        context['TAG_MAX_LEN'] = TAG_MAX_LEN
        return context


class SearchResultsView(BasePageView):

    template_name = "results.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.GET.get('q'):
            return redirect('front')
        return super(SearchResultsView, self).dispatch(request, *args, **kwargs)

    def getResults(self, request):
        query = request.GET.get('q')
        results = engine.query(query)
        return group(results, "results", True)

    def get_context_data(self, **kwargs):
        context = super(SearchResultsView, self).get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q')
        context['results'] = paginate(self.request,
                             self.getResults(self.request))
        return context


class ProfileView(BasePageView):
    
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        user_profile = get_object_or_404(User, username=self.kwargs\
                                                            .get('username'))
        if not user_profile.is_active:
            raise Http404
        context['username'] = user_profile
        context['score'] = UserScore.objects.get(user=user_profile).score
        starred = UserFavorite.objects.filter(user=user_profile)
        context['starred_total'] = starred.count()
        context['starred_recent'] = group(starred
                                              .order_by('-date_favorited')[:8],
                                              "starred", True)
        added = Gif.objects.filter(user_added=user_profile)
        context['added_total'] = added.count()
        context['added_recent'] = group(added.order_by('-date_added')[:8],
                                            "added")
        return context


class ProfileStarredView(BasePageView):

    template_name = "profile_starred.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileStarredView, self).get_context_data(**kwargs)
        user_profile = get_object_or_404(User, username=self.kwargs\
                                                   .get('username'))
        if not user_profile.is_active:
            raise Http404
        context['username'] = user_profile
        starred = group(UserFavorite.objects.filter(user=user_profile)\
                            .order_by('-date_favorited'), "starred", True)
        context['starred'] = paginate(self.request, starred)
        context['starred_total'] = starred.count()
        return context


class ProfileAddedView(BasePageView):

    template_name = "profile_added.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileAddedView, self).get_context_data(**kwargs)
        user_profile = get_object_or_404(User, username=self.kwargs\
                                                   .get('username'))
        if not user_profile.is_active:
            raise Http404
        context['username'] = user_profile
        added = group(Gif.objects.filter(user_added=user_profile)\
                                    .order_by('-date_added'), "added")
        context['added'] = paginate(self.request, added)
        context['added_total'] = added.count()
        return context


## auxiliary

class AboutPageView(BasePageView):

    template_name = "about.html"


class TermsPageView(BasePageView):

    template_name = "terms.html"


class LegalPageView(BasePageView):

    template_name = "legal.html"


class AccountPreferencesView(BasePageView):

    template_name = "account_preferences.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('front')
        return super(AccountPreferencesView, self)\
                                            .dispatch(request, *args, **kwargs)



## accounts

class RegistrationView(BaseRegistrationView, BasePageView):
    
    template_name="registration/registration_form.html"
    

class RegistrationCompleteView(BasePageView):
    
    template_name = "registration/registration_complete.html"


class RegistrationClosedView(BasePageView):
    
    template_name = "registration/registration_closed.html"


class ActivationView(BaseActivationView, BasePageView):

    pass


class ActivationCompleteView(BasePageView):

    template_name = "registration/activation_complete.html"


class PasswordChangeView(BasePageView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return auth_views.password_change(request, 
                         post_change_redirect=reverse('password_change_done'),
                         extra_context=self.get_context_data())
        else:
            return redirect('front')
    

class PasswordChangeDoneView(BasePageView):
    
    def get(self, request):
        if request.user.is_authenticated():
            return auth_views.password_change_done(request, 
                                         extra_context=self.get_context_data())
        else:
            return redirect('front')


class PasswordResetView(BasePageView):
    
    def dispatch(self, request, *args, **kwargs):
        return auth_views.password_reset(request, 
                             post_reset_redirect=reverse('password_reset_done'), 
                             extra_context=self.get_context_data())


class PasswordResetDoneView(BasePageView):
    
    def get(self, request):
        return auth_views.password_reset_done(request, 
                                         extra_context=self.get_context_data())


class PasswordResetConfirmView(BasePageView):
    
    def dispatch(self, request, uidb36=None, token=None):
        return auth_views.password_reset_confirm(request, uidb36=uidb36, 
                       token=token,
                       post_reset_redirect=reverse('password_reset_complete'), 
                       extra_context=self.get_context_data())


class PasswordResetCompleteView(BasePageView):
    
    def get(self, request):
        return auth_views.password_reset_complete(request, 
                                         extra_context=self.get_context_data())


class AccountDeleteView(BasePageView):

    template_name = "registration/account_delete_form.html" 

    def __init__(self, *args, **kwargs):
        self.form_error = None
        super(AccountDeleteView, self).__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('front')
        return super(AccountDeleteView, self).dispatch(request, *args, **kwargs)
    
    def post(self, request):
        try:
            username = request.POST['username']
            password = request.POST['password']
        except MultiValueDictKeyError:
            return redirect('front')
        user = authenticate(username=username, password=password)
        if user is not None and user == request.user:
            django_logout(request)
            user.is_active = False
            user.save()
            return redirect('account_delete_complete')
        else:
            self.form_error = '''That username and password are incorrect
                                 for the currently logged-in user.'''
            return redirect('account_delete')

    def get_context_data(self, **kwargs):
        context = super(AccountDeleteView, self).get_context_data(**kwargs)
        context['form_error'] = self.form_error
        return context


class AccountDeleteCompleteView(BasePageView):
    
    template_name = "registration/account_delete_complete.html"


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
        else: # user is not active
            messages.success(request, 1)
            return redirect(request.META['HTTP_REFERER'])
    else: # user did not sucessfully authenticate
        messages.success(request, 2)
        return redirect(request.META['HTTP_REFERER'])

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
            if not user.canTag():
                return accessError("This user doesn't have the permission to "
                                   "vote on tags.")
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
            if not user.canTag():
                return accessError("This user doesn't have the permission to "
                                   "add tags.")
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
            if not user.canAddGif():
                return accessError("This user doesn't have the permission to "
                                   "add GIFs.")
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
