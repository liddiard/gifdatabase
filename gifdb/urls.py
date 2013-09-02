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
    url(r'^$', frontPage),
    url(r'^login/$', doLogin),
    url(r'^results/$', searchResults),
    url(r'^admin/', include(admin.site.urls)),
)
