from django.conf.urls import patterns, include, url
import CronWeibo
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^loginSina/', 'CronWeibo.views.loginSina'),
    url(r'^loginTencent/', 'CronWeibo.views.loginTencent'),
    url(r'^sinacallback/', 'CronWeibo.views.sinacallback'),
    url(r'^tencentcallback/', 'CronWeibo.views.tencentcallback'),
    url(r'^clean_auth/', 'CronWeibo.views.clean_auth'),
   	url(r'^send/', 'CronWeibo.views.send'),
   	url(r'^re_auth_sina/', 'CronWeibo.views.re_auth_sina'),
   	url(r'^re_auth_tencent/', 'CronWeibo.views.re_auth_tencent'),
   	url(r'^send_reauth_mail/', 'CronWeibo.views.send_reauth_mail'),
   	url(r'^clean_cached_items/', 'CronWeibo.views.clean_cached_items'),
   	url(r'^$', 'CronWeibo.views.index'),
)