from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from search.views import * # bad practice

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'gifdb.views.home', name='home'),
    # url(r'^gifdb/', include('gifdb.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # front page
    url(r'^$', frontPage, name="front"),

    # state modification
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout, name="logout"),
    
    # api
    url(r'^api/tag-vote/$', ajaxTagVote, name="vote"),
    url(r'^api/tagvote-get/$', ajaxGetTagVote, name="get_tagvote"),
    url(r'^api/tag-add/$', ajaxAddTag, name="tag_add"),
    url(r'^api/tag-erase/$', ajaxEraseTag, name="tag_erase"),
    url(r'^api/star-get/$', ajaxGetStarView, name="star"),
    url(r'^api/star-add/$', ajaxAddStar, name="star_add"),
    url(r'^api/star-remove/$', ajaxRemoveStar, name="star_remove"),
    url(r'^api/gif-check/$', ajaxCheckValidGif, name="check_gif"),
    url(r'^api/gif-add/$', ajaxAddGif, name="add_gif"),
    
    # pages
    url(r'^search/$', searchResults, name="search_results"),
    url(r'^user/(?P<username>\w+)/$', profile, name="profile"),
    url(r'^user/(?P<username>\w+)/starred/$', profileStarred,
        name="profile_starred"),
    url(r'^user/(?P<username>\w+)/added/$', profileAdded,
        name="profile_added"),

   # admin
    url(r'^admin/', include(admin.site.urls)),
)
