from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()
from django.http import HttpResponse
from django.contrib.auth.views import login, logout

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^loginSina/(\S+)/$', 'Auth.views.loginSina'),
    url(r'^sinacallback/', 'Auth.views.sinacallback'),
    url(r'^clean_auth/', 'Auth.views.clean_auth'),
    url(r'^re_auth_sina/', 'Auth.views.re_auth_sina'),
    url(r'^clean_cached_items/', 'Auth.views.clean_cached_items'),
    url(r'^$', 'MoeWiki.views.index'),
    url(r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /",
        mimetype="text/plain")),
    url(r'^accounts/login/', login),
    url(r'^verify/', 'MoeWiki.views.verify')
)
