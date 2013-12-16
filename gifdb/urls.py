from django.conf.urls import patterns, include, url
from django.contrib import admin
from search import views

admin.autodiscover()

urlpatterns = patterns('',

    # front page
    url(r'^$', views.FrontPageView.as_view(), name="front"),

    # state modification
    url(r'^login/$', views.login, name="login"),
    url(r'^logout/$', views.logout, name="logout"),
    
    # api
    url(r'^api/tag-vote/$', views.AjaxTagVote.as_view(), name="vote"),
    url(r'^api/tagvote-get/$', views.AjaxGetTagVote.as_view(), name="get_tagvote"),
    url(r'^api/tag-add/$', views.AjaxAddTag.as_view(), name="tag_add"),
    url(r'^api/tag-erase/$', views.AjaxEraseTag.as_view(), name="tag_erase"),
    url(r'^api/star-get/$', views.AjaxGetStar.as_view(), name="star"),
    url(r'^api/star-add/$', views.AjaxAddStar.as_view(), name="star_add"),
    url(r'^api/star-remove/$', views.AjaxRemoveStar.as_view(), name="star_remove"),
    url(r'^api/gif-check/$', views.AjaxCheckValidGif.as_view(), name="check_gif"),
    url(r'^api/gif-add/$', views.AjaxAddGif.as_view(), name="add_gif"),
    url(r'^api/flag-add/$', views.AjaxAddFlag.as_view(), name="add_flag"),
    
    # pages
    url(r'^search/$', views.SearchResultsView.as_view(), name="search_results"),
    url(r'^user/(?P<username>\w+)/$', views.ProfileView.as_view(),
        name="profile"),
    url(r'^user/(?P<username>\w+)/starred/$', views.ProfileStarredView.as_view(),
        name="profile_starred"),
    url(r'^user/(?P<username>\w+)/added/$', views.ProfileAddedView.as_view(),
        name="profile_added"),
    url(r'^about/$', views.AboutPageView.as_view(), name="about"),
    url(r'^faq/$', views.FaqPageView.as_view(), name="faq"),
    url(r'^terms/$', views.TermsPageView.as_view(), name="terms"),

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # accounts
    (r'^account/', include('gifdb.urls_account')),
)

handler404 = "search.views.Error404View.as_view()"
