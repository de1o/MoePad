from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()
from django.http import HttpResponse


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^loginSina/(\S+)/$', 'CronWeibo.views.loginSina'),
    url(r'^loginTencent/(\S+)/$', 'CronWeibo.views.loginTencent'),
    url(r'^send/', 'CronWeibo.views.send'),
    url(r'^retweet/(\S+)/', 'CronWeibo.views.retweet'),
    url(r'^send_reauth_mail/', 'CronWeibo.views.send_reauth_mail'),
    url(r'^sinacallback/', 'Auth.views.sinacallback'),
    url(r'^tencentcallback/', 'Auth.views.tencentcallback'),
    url(r'^clean_auth/', 'Auth.views.clean_auth'),
    url(r'^re_auth_sina/', 'Auth.views.re_auth_sina'),
    url(r'^re_auth_tencent/', 'Auth.views.re_auth_tencent'),
    url(r'^clean_cached_items/', 'Auth.views.clean_cached_items'),
    url(r'^$', 'CronWeibo.views.index'),
    url(r'^robots\.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", mimetype="text/plain")),
)
