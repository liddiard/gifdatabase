import json, re
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.cache import cache
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import (authenticate, login as django_login,
                                 logout as django_logout)
from django.contrib.auth import views as auth_views
from django.utils.datastructures import MultiValueDictKeyError
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView

from taggit.models import Tag
from registration.backends.default.views import (ActivationView as
                                                 BaseActivationView,
                                                 RegistrationView as
                                                 BaseRegistrationView)

from gifdb.settings.base import OBFUSCATION_KEY
from search import engine
from search.models import (TAG_MAX_LEN, group, queryRecentGifs, 
                           queryRecommendedGifs, User, UserFavorite, Gif, 
                           TagInstance, UserScore, TagVote, Flag)
from search.forms import ConfirmCurrentUserForm
from search.image import imgFromUrl, isAnimated


# utility functions

def paginate(request, queryset):
    paginator = Paginator(queryset, 19) # num results per page
    page = request.GET.get('page')
    try:
        qp = paginator.page(page)
    except PageNotAnInteger:
        qp = paginator.page(1)
    except EmptyPage:
        qp = paginator.page(paginator.num_pages)
    return qp

def unmask_uid(uid):
    try:
        return int(uid) ^ OBFUSCATION_KEY
    except ValueError:
        return None 
        # fails silently, but error will be caught when lookup by pk fails


# pages

## inheritable

class BasePageView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(BasePageView, self).get_context_data(**kwargs)
        user = self.request.user
        context['TAG_MAX_LEN'] = TAG_MAX_LEN
        context['recent_gifs'] = cache.get('recent_gifs', queryRecentGifs)
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
            recommended_gifs = cache.get('recommended_gifs', 
                                         queryRecommendedGifs)
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


class FaqPageView(BasePageView):

    template_name = "faq.html"


class TermsPageView(BasePageView):

    template_name = "terms.html"


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


class AccountDeleteView(FormView):

    template_name = "registration/account_delete_form.html" 
    form_class = ConfirmCurrentUserForm
    success_url = reverse_lazy('account_delete_complete')

    def get_form_kwargs(self):
        kwargs = super(AccountDeleteView, self).get_form_kwargs()
        kwargs.update({
            'request' : self.request
        })
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return redirect('front')
        return super(AccountDeleteView, self).dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.cleaned_data.get('user')
        user.is_active = False
        user.save()
        django_logout(self.request)
        return redirect('account_delete_complete')


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


# error handling

class Error404View(BasePageView):
    
    template_name = "404.html"


# ajax api

class AuthenticatedAjaxView(View):

    def dispatch(self, request, *args, **kwargs):
        if request.is_ajax():
            if request.user.is_authenticated():
                return super(AuthenticatedAjaxView, self).dispatch(request, 
                                                              *args, **kwargs)
            else: 
                return self.authenticationError()
        else:
            raise Http404

    def jsonResponse(self, **kwargs):
        return HttpResponse(json.dumps(kwargs), content_type="application/json")

    def error(self, error_type, message):
        return self.jsonResponse(result=1, error=error_type, message=message)

    def authenticationError(self):
        return self.error("AuthenticationError", "User is not authenticated.")

    def accessError(self, message):
        return self.error("AccessError", message)

    def keyError(self, message):
        return self.error("KeyError", message)

    def doesNotExist(self, message):
        return self.error("DoesNotExist", message)

    def validationError(self, message):
        return self.error("ValidationError", message)


# ajax api

class AjaxTagVote(AuthenticatedAjaxView):
    
    def post(self, request):  
        def safeVote(user, tag, up):
            try: # TODO: enforce m2m uniqueness on model validation as well
                tv = TagVote.objects.filter(user=user).get(tag=tag)
                tv.up = up
            except TagVote.DoesNotExist:
                tv = TagVote(user=user, tag=tag, up=up)
            finally:
                tv.save()
        user = request.user
        if not user.canTag():
            return self.accessError("This user doesn't have the permission to "
                               "vote on tags.")
        try:
            tag_id = unmask_uid(request.POST['tag'])
            set = request.POST['set']
        except KeyError:
            return self.keyError("Required keys (tag, set) not found in "
                                 "request.")
        try:
            tag = TagInstance.objects.get(pk=tag_id)
        except TagInstance.DoesNotExist:
            return self.doesNotExist("Tag with id %s was not found." % tag_id)
        if user == tag.user_added:
            return self.accessError("User cannot vote on a tag they created "
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
                return self.doesNotExist("Could not unset TagVote because "
                                         "TagVote doesn't exist.")
        return self.jsonResponse(result=0, tag_id=tag.uid(), 
                                 tag_name=tag.tag.name, set=set)


class AjaxGetTagVote(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        try:
            tag_uid = request.POST['tag']
        except KeyError:
            return self.keyError("Required key (tag) not found in request.")
        else:
            tag_id = unmaskUid(tag_uid)
        try:
            tv = TagVote.objects.filter(user=user).get(tag=tag_id)
        except TagVote.DoesNotExist:
            return self.jsonResponse(result=0, tag=tag_uid, vote=0)
        if tv.up:
            return self.jsonResponse(result=0, tag=tag_uid, vote=1)
        else:
            return self.jsonResponse(result=0, tag=tag_uid, vote=-1)


class AjaxAddTag(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        if not user.canTag():
            return self.accessError("This user doesn't have the permission to "
                               "add tags.")
        try:
            gif_id = unmask_uid(request.POST['gif'])
            tag_name = request.POST['tag']
        except KeyError:
            return self.keyError("Required keys (gif, tag) not found in "
                                 "request.")
        tag_name = tag_name.lower()
        pattern = re.compile("^[a-z0-9\. '-]+$")
        if not pattern.match(tag_name):
            return self.validationError("Tag contains invalid characters.")
        if len(tag_name) > TAG_MAX_LEN:
            return self.validationError("Tag length is greater than max "
                                   "allowed length of %s chars." % TAG_MAX_LEN)
        try:
            gif = Gif.objects.get(pk=gif_id)
        except Gif.DoesNotExist:
            return self.doesNotExist("Could not add tag to gif because gif "
                                     "matching id %s doesn't exist." % gif_id)
        if gif.tags.count() > 11:
            return self.accessError("The gif associated with this tag already "
                                    "has the maximum number of tags.")
        t = Tag.objects.get_or_create(name=tag_name)[0]
        ti, created = TagInstance.objects.get_or_create(tag=t,
                                                        content_object=gif)
        print ti
        if created:
            ti.user_added = user
            ti.save()
        else:
            pass # tag already exists on this GIF, do nothing
        return self.jsonResponse(result=0, taginstance=ti.uid())


class AjaxEraseTag(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        try:
            tag_id = unmask_uid(request.POST['tag'])
        except KeyError:
            return self.keyError("Required key (tag) not found in request.")
        try:
            ti = TagInstance.objects.get(pk=tag_id)
        except TagInstance.DoesNotExist:
            return self.doesNotExist("Could not delete tag because tag "
                                     "matching id %s doesn't exist." % tag_id)
        if ti.hasBeenVotedOn():
            return self.accessError("This tag has already been voted on and "
                                    "thus cannot be user-erased.")
        if ti.content_object.tags.count() < 5:
            return self.accessError("The gif you are trying to tag already "
                                    "has the minimum number of tags.")
        else:
            if ti.user_added == user:
                ti.delete()
                return self.jsonResponse(result=0, message="Deleted tag.")
            else:
                return self.accessError("The requesting user does not have "
                                        "permission to delete this tag.")


class AjaxGetStar(AuthenticatedAjaxView):
    
    def post(self, request):
        user = request.user
        try:
            gif_id = unmask_uid(request.POST['gif'])
        except KeyError:
            return self.keyError("Required key (gif) not found in request.")
        try:
            gif = Gif.objects.get(pk=gif_id)
        except Gif.DoesNotExist:
            return self.doesNotExist("Could not get UserFavorite because Gif "
                                     "matching id %s does not exist." % gif_id)
        try:
            UserFavorite.objects.get(user=user, gif=gif)
            return self.jsonResponse(result=0, star=1)
        except UserFavorite.DoesNotExist:
            return self.jsonResponse(result=0, star=0)    


class AjaxAddStar(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        try:
            gif_id = unmask_uid(request.POST['gif'])
        except KeyError:
            return self.keyError("Required key (gif) not found in request.")
        try:
            gif = Gif.objects.get(pk=gif_id)
        except Gif.DoesNotExist:
            return self.doesNotExist("Could not create UserFavorite because "
                                "Gif matching id %s does not exist." % gif_id)
        uf = UserFavorite.objects.get_or_create(user=user, gif=gif)[0]
        return self.jsonResponse(result=0, userfavorite=uf.pk)


class AjaxRemoveStar(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        try:
            gif_id = unmask_uid(request.POST['gif'])
        except KeyError:
            return self.keyError("Required key (gif) not found in request.")
        try:
            uf = UserFavorite.objects.get(user=user, gif=gif_id)
        except Gif.DoesNotExist:
            return self.doesNotExist("Could not create UserFavorite because "
                                 "Gif matching id %s does not exist." % gif_id)
        if uf.user == user:
            uf.delete()
            return self.jsonResponse(result=0, message="Deleted UserFavorite.")
        else:
            return self.accessError("The requesting user does not match the "
                                    "user who created the UserFavorite.")


class AjaxCheckValidGif(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        try:
            filename = request.POST['filename']
        except KeyError:
            return self.keyError("Required key (filename) not found in "
                                 "request.")
        preexisting = request.POST.get('preexisting', False)
        if preexisting:
            try:
                gif = Gif.objects.get(filename=filename)
            except Gif.DoesNotExist:
                return self.doesNotExist("GIF matching filename does not exist.")
            else:
                return self.jsonResponse(result=0, url=url)
        else:
            try:
                gif = Gif.objects.get(filename=filename)
            except Gif.DoesNotExist:
                url = "http://i.imgur.com/%s.gif" % filename
                if isAnimated(imgFromUrl(url)):
                    return self.jsonResponse(result=0, url=url)
                else:
                    return self.error("InvalidFileError", "Image %s is not an "
                                      "animated gif." % filename)
            else:
                return self.error("AlreadyExistsError", "Gif %s already exists" %\
                             filename)


class AjaxAddGif(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        if not user.canAddGif():
            return self.accessError("This user doesn't have the permission to "
                                    "add GIFs.")
        try:
            filename = request.POST['filename']
            tags = request.POST.getlist('tags[]')
        except KeyError:
            return self.keyError("Required keys (filename, tags) not found in "
                                 "request.")
        try:
            gif = Gif.objects.get(filename=filename)
            return self.error("AlreadyExistsError", "Gif %s already exists" %\
                              filename)
        except Gif.DoesNotExist:
            pattern = re.compile("^[a-z0-9\. '-]+$")
            valid_tags = [tag_name.lower() for tag_name in tags if 
                          pattern.match(tag_name) and
                          len(tag_name) < TAG_MAX_LEN]
            if len(valid_tags) < 4:
                return self.validationError("Only %s of the tags were valid. "
                                           "4 are required." % len(valid_tags))
            url = "http://i.imgur.com/%s.gif" % filename
            if isAnimated(imgFromUrl(url)):
                gif = Gif(filename=filename, user_added=user)
                gif.save()
                for tag_name in valid_tags:
                    t = Tag.objects.get_or_create(name=tag_name)[0]
                    ti = TagInstance(tag=t, user_added=user, content_object=gif)
                    ti.save()
                return self.jsonResponse(result=0, gif=gif.uid())
            else:
                return self.error("InvalidFileError", "Image %s is not an "
                                  "animated gif." % filename)


class AjaxAddFlag(AuthenticatedAjaxView):

    def post(self, request):
        user = request.user
        if not user.canAddGif():
            return self.accessError("This user doesn't have the permission to "
                                    "flag GIFs.")
        try:
            gif_id = unmask_uid(request.POST['gif'])
            flag_type = request.POST['type']
        except KeyError:
            return self.keyError("Required keys (gif, type) not found in "
                                 "request.")
        filename = request.POST.get('filename') # this one won't throw an error
                                                # b/c it's optional, depending
                                                # on flag type
        try:
            gif = Gif.objects.get(pk=gif_id)
        except Gif.DoesNotExist:
            return self.doesNotExist("Couldn't flag GIF because GIF matching "
                                     "given id doesn't exist.")
        if flag_type == 'du': # duplicate
            if filename is None:
                return keyError("Required key (filename) not found in request.")
            try:
                duplicate = Gif.objects.get(filename=filename)
            except Gif.DoesNotExist:
                return self.doesNotExist("Couldn't flag GIF because duplicate "
                                         "GIF matching filename doesn't exist")
            flag = Flag.objects.get_or_create(user_flagged=user, gif=gif,
                                              reason=flag_type, 
                                              duplicate=duplicate)[0]
            return self.jsonResponse(result=0, flag=flag.pk)
        elif flag_type == 'mi' or flag_type == 'in': # missing/inappropriate
            flag = Flag.objects.get_or_create(user_flagged=user, gif=gif, 
                                              reason=flag_type)[0]
            return self.jsonResponse(result=0, flag=flag.pk)
        else:
            return validationError("'%s' is not a valid flag type." % flag_type)
