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

    # Uncomment the next line to enable the admin:
    url(r'^$', frontPage, name="main"),
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout, name="logout"),
    url(r'^vote/$', ajaxTagVote, name="vote"),
    url(r'^results/$', searchResults, name="search_results"),
    url(r'^user/(?P<username>\w+)/$', profile, name="profile"),
    url(r'^user/(?P<username>\w+)/starred/$', profileStarred,
        name="profile_starred"),
    url(r'^admin/', include(admin.site.urls)),
)
