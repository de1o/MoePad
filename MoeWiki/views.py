# -*- coding: utf-8 -*-
import feedparser
import datetime
import logging

from django.http import HttpResponse, Http404
from django.shortcuts import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

from MoePad.mputils import rs
from forms import MPConfigForm
from MoeWiki.models import RecentUpdateItems

log = logging.getLogger('moepad')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # new user created
            return HttpResponseRedirect("/accounts/login/")
    else:
        form = UserCreationForm()
    return render_to_response("registration/register.html",
                              {'form': form},
                              context_instance=RequestContext(request))


@login_required
def index(request):
    if request.method == 'POST':
        form = MPConfigForm(request.POST)
        if form.is_valid():
            rs.hmset("MoePadConf", request.POST)
        return render(request, "index.html", {"form": form})
    else:
        data = rs.hgetall("MoePadConf")
        print data
        form = MPConfigForm(initial=data)
        return render(request, "index.html", {"form": form})


def verify(request):
    if request.method == 'POST':
        print request.POST
        for key in request.POST.keys():
            if 'on' in request.POST[key]:
                RecentUpdateItems.objects.filter(title=key).update(
                    itemState=RecentUpdateItems.VERIFIED)

        return generateUnverifiedPage(request)
    else:
        return generateUnverifiedPage(request)


def generateUnverifiedPage(request):
    unverified_items_rec = RecentUpdateItems.objects.filter(
        itemState=RecentUpdateItems.VERIFYING_NEW)
    unverified_items = [rec.title.encode('utf-8')
                        for rec in unverified_items_rec]
    c = RequestContext(request, {"unverified_items": unverified_items})
    return render_to_response('verify.html', c)
