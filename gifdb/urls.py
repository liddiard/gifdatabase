from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from search import views

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'gifdb.views.home', name='home'),
    # url(r'^gifdb/', include('gifdb.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # front page
    url(r'^$', views.FrontPageView.as_view(), name="front"),

    # state modification
    url(r'^login/$', views.login, name="login"),
    url(r'^logout/$', views.logout, name="logout"),
    
    # api
    url(r'^api/tag-vote/$', views.ajaxTagVote, name="vote"),
    url(r'^api/tagvote-get/$', views.ajaxGetTagVote, name="get_tagvote"),
    url(r'^api/tag-add/$', views.ajaxAddTag, name="tag_add"),
    url(r'^api/tag-erase/$', views.ajaxEraseTag, name="tag_erase"),
    url(r'^api/star-get/$', views.ajaxGetStarView, name="star"),
    url(r'^api/star-add/$', views.ajaxAddStar, name="star_add"),
    url(r'^api/star-remove/$', views.ajaxRemoveStar, name="star_remove"),
    url(r'^api/gif-check/$', views.ajaxCheckValidGif, name="check_gif"),
    url(r'^api/gif-add/$', views.ajaxAddGif, name="add_gif"),
    
    # pages
    url(r'^search/$', views.SearchResultsView.as_view(), name="search_results"),
    url(r'^user/(?P<username>\w+)/$', views.ProfileView.as_view(),
        name="profile"),
    url(r'^user/(?P<username>\w+)/starred/$', views.ProfileStarredView.as_view(),
        name="profile_starred"),
    url(r'^user/(?P<username>\w+)/added/$', views.ProfileAddedView.as_view(),
        name="profile_added"),
    url(r'^about/$', views.AboutPageView.as_view(), name="about"),
    url(r'^terms/$', views.TermsPageView.as_view(), name="terms"),
    url(r'^legal/$', views.LegalPageView.as_view(), name="legal"),

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # other
    (r'^account/', include('registration.backends.default.urls')),
)
