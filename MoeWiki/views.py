# -*- coding: utf-8 -*-
import feedparser
from MoeWiki.models import WikiItems, AlreadlyRetweeted, MoePadConfig, RecentUpdateItems
from Forbidden.models import ForbiddenWikiItems
from Auth.models import WeiboAuth
from BeautifulSoup import BeautifulSoup
from django.utils import timezone
import datetime
import urllib2
import urllib
from Auth.views import getWeiboAuthedApi
import traceback
import logging

from django.http import HttpResponse, Http404
from django.shortcuts import *
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.context_processors import csrf
from django import forms

log = logging.getLogger('moepad')

def mystrptime(str):
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ")


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # new user created
            return HttpResponseRedirect("/accounts/login/")
    else:
        form = UserCreationForm()

    # c = RequestContext(request, {'form': form})
    # temp = get_template("registration/register.html")
    # return HttpResponse(temp.render(c))
    return render_to_response("registration/register.html", 
        {'form': form},
        context_instance=RequestContext(request))


@login_required
def index(request):
    if request.method == 'POST':
        # TODO validate data posted
        return configCommitProc(request)
    else:
        return renderIndex(request)

def renderIndex(request):
    field_list = generateFieldListFromConfig()
    c = RequestContext(request, {"field_list": field_list})
    return render_to_response('index.html', c)


def configCommitProc(request):
    print request.POST, '----------------'
    error_list = []
    print request.POST.get('moesite'), '--------------'
    if request.POST.get('moesite') == "":
        error_list.append("请输入更新程序所在域名地址")

    if request.POST.get('sameiteminterval') == "":
        error_list.append("请输入条目刷出后禁止再次刷出的时长")

    if error_list:
        c = RequestContext(request, {"field_list": generateFieldListFromConfig(),
                                "error_list": error_list})
        return render_to_response("index.html", c)
    configHandler = MoePadConfig.objects.all()
    if configHandler:
        configHandler.update(
            SinaAppKey=request.POST.get("sinaappkey"),
            sinaAppSecret=request.POST.get("sinaappsecret"),
            TencentAppKey=request.POST.get("tencentappkey"),
            TencentAppSecret=request.POST.get("tencentappsecret"),
            MoeWebsite=request.POST.get("moesite"),
            sameItemInterval=request.POST.get("sameiteminterval")
            )
    else:
        configHandler = MoePadConfig(
            SinaAppKey=request.POST.get("sinaappkey"),
            sinaAppSecret=request.POST.get("sinaappsecret"),
            TencentAppKey=request.POST.get("tencentappkey"),
            TencentAppSecret=request.POST.get("tencentappsecret"),
            MoeWebsite=request.POST.get("moesite"),
            sameItemInterval=request.POST.get("sameiteminterval"))
        configHandler.save()
    field_list = generateFieldListFromConfig()
    c = RequestContext(request, {"field_list": field_list})
    return render_to_response('index.html', c)


def generateFieldListFromConfig():
    try:
        config = MoePadConfig.objects.all()[0]
        SinaAppKey = config.SinaAppKey
        sinaAppSecret = config.sinaAppSecret
        TencentAppKey = config.TencentAppKey
        TencentAppSecret = config.TencentAppSecret
        MoeWebsite = config.MoeWebsite
        sameItemInterval = config.sameItemInterval

    except:
        SinaAppKey = ''
        sinaAppSecret = ''
        TencentAppKey = ''
        TencentAppSecret = ''
        MoeWebsite = ''
        sameItemInterval = ''

    field_list = []
    field_list.append({"input_id": "sinaappkey", "field_name": "Sina App Key:", "value": SinaAppKey})
    field_list.append({"input_id": "sinaappsecret", "field_name": "Sina App Secret:", "value": sinaAppSecret})
    field_list.append({"input_id": "tencentappkey", "field_name": "Tencent App Key:", "value": TencentAppKey})
    field_list.append({"input_id": "tencentappsecret", "field_name": "Tencent App Secret:", "value": TencentAppSecret})
    field_list.append({"input_id": "moesite", "field_name": "MoePad程序所在域名*:", "value": MoeWebsite})
    field_list.append({"input_id": "sameiteminterval", "field_name": "已刷出条目禁止时长(小时)*:", "value": sameItemInterval})
    return field_list


def verify(request):
    if request.method == 'POST':
        print request.POST
        for key in request.POST.keys():
            if 'on' in request.POST[key]:
                RecentUpdateItems.objects.filter(title=key).update(itemState=RecentUpdateItems.VERIFIED)

        return generateUnverifiedPage(request)
    else:
        return generateUnverifiedPage(request)

def generateUnverifiedPage(request):
    unverified_items_rec = RecentUpdateItems.objects.filter(itemState=RecentUpdateItems.VERIFYING_NEW)
    unverified_items = [rec.title.encode('utf-8') for rec in unverified_items_rec]
    c = RequestContext(request, {"unverified_items": unverified_items})
    return render_to_response('verify.html', c)