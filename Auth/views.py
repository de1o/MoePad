# Create your views here.
import logging
import weibo
from Auth.models import WeiboAuth
import qqweibo
import pickle
from django.http import HttpResponse
from django.shortcuts import *
from MoeWiki.models import WikiItems, MoePadConfig
from django.contrib.auth.decorators import login_required

from MoePad.mputils import sub_dict, rs
from MoePad.mpconfig import MPConf

log = logging.getLogger('moepad')


SinaAppKey = MPConf.SinaAppKey
SinaAppSecret = MPConf.SinaAppSecret
MoePadSite = MPConf.Domain


class WeiboAuthInfo(object):
    def __init__(self, user_type):
        super(WeiboAuthInfo, self).__init__()
        args = locals()
        args.pop("self")
        for key in args.keys():
            setattr(self, key, args[key])

    def set(self, access_token, expires_in, user_type, uid):
        args = locals()
        args.pop("self")
        for key in args.keys():
            setattr(self, key, args[key])

    def load():
        pass

    def save(self):
        pass

    def clean(self):
        pass


class WeiboAuthInfoRedis(WeiboAuthInfo):
    def __init__(self, user_type):
        super(WeiboAuthInfoRedis, self).__init__(user_type)
        self.mckey = "WeiboAuth" + user_type

    def load(self):
        args = rs.get(self.mckey)
        if args:
            for key in args.keys():
                setattr(self, key, args[key])

    def save(self):
        print self.__dict__
        confs = sub_dict(self.__dict__,
                         ['uid', 'access_token', 'expires_in', 'user_type'])
        rs.hmset(self.mckey, confs)
        rs.expire(confs['expires_in'])

    def clean(self):
        rs.hdel(self.mckey)

OriWeiboAuth = WeiboAuthInfoRedis("original")
RtWeiboAuth = WeiboAuthInfoRedis("retweet")


def authSina(code):
    client = weibo.APIClient(SinaAppKey, SinaAppSecret,
                             MoePadSite+"/sinacallback")
    r = client.request_access_token(code)
    client.set_access_token(r.access_token, r.expires_in)
    ruid = client.account.get_uid.get()
    #can get user type when callback from sina
    #so save the type in memcache, as long as
    #only on account get oauthed at a time, this works
    current_user_type = rs.get("current_user_type")
    print current_user_type
    if current_user_type == "original":
        WeiboAuthObj = OriWeiboAuth
    elif current_user_type == "retweet":
        WeiboAuthObj = RtWeiboAuth
    else:
        log.error("invalid callback user type autSina")
        raise Exception
    WeiboAuthObj.set(
        access_token=r.access_token,
        expires_in=r.expires_in,
        user_type=current_user_type, uid=ruid.uid)
    WeiboAuthObj.save()
    return r.access_token, r.expires_in


def authSinaUrl():
    client = weibo.APIClient(
        SinaAppKey, SinaAppSecret, MoePadSite+"/sinacallback")
    return client.get_authorize_url()


@login_required
def sinacallback(request):
    code = request.GET['code']
    access_token, expires_in = authSina(code)
    c = {"information": "auth info saved"}
    return render_to_response("info.html", c)


@login_required
def clean_auth(request):
    WeiboAuthObj.clean()
    c = {"information": "auth info has been cleaned"}
    return render_to_response("info.html", c)


@login_required
def re_auth_sina(requset):
    WeiboAuthObj.clean()
    return redirect(authSinaUrl())


@login_required
def clean_cached_items(requset):
    cachedItems = WikiItems.objects.all()
    for item in cachedItems:
        if not item.was_add_recently():
            item.delete()

    c = {"information": "ok"}
    return render_to_response("info.html", c)


def getWeiboAuthedApi(source, user_type):
    if user_type == "original":
        weiboData = OriWeiboAuth
    elif user_type == "retweet":
        weiboData = RtWeiboAuth
    else:
        log.error("invalid user type getWeiboAuthedApi")
        raise e

    if source == 'sina':
        client = weibo.APIClient(
            SinaAppKey, SinaAppSecret, MoePadSite+"/sinacallback")
        client.set_access_token(weiboData.access_token, weiboData.expires_in)

        return client


@login_required
def loginSina(request, user_type):
    rs.set("current_user_type", user_type)
    return redirect(authSinaUrl())
