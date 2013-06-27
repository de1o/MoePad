# Create your views here.
import mpconfig
from mpconfig import mc
import logging
import weibo
from Auth.models import WeiboAuth
import qqweibo
import pickle
from django.http import HttpResponse
from django.shortcuts import *
from MoeWiki.models import WikiItems

SinaAppKey = mpconfig.SinaAppKey
SinaAppSecret = mpconfig.SinaAppSecret
TencentAppKey = mpconfig.TencentAppKey
TencentAppSecret = mpconfig.TencentAppSecret
MoeWebsite = mpconfig.MoeWebsite
if not MoeWebsite.startswith("http"):
    raise Exception


log = logging.getLogger('moepad')


def authSina(code):
    client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/sinacallback")
    r = client.request_access_token(code)

    client.set_access_token(r.access_token, r.expires_in)
    ruid = client.account.get_uid.get()
    user_type = mc.get('user_type')
    mc.set('user_type', 'invalid')
    sinaData = WeiboAuth(access_token=r.access_token, expires_in=r.expires_in, source="sina",
                         user_type=user_type, uid=ruid.uid)
    sinaData.save()
    return r.access_token, r.expires_in


def authSinaUrl():
    client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/sinacallback")
    return client.get_authorize_url()


def authTencentUrl():
    auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret, callback=MoeWebsite+"/tencentcallback")
    url = auth.get_authorization_url()
    f = open('tx_rt', 'wb')
    f.write(pickle.dumps(auth.request_token))
    f.close()
    return url


def sinacallback(request):
    code = request.GET['code']
    access_token, expires_in = authSina(code)
    return HttpResponse("auth info saved")


def tencentcallback(request):
    verifier = request.GET['oauth_verifier']
    auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret, callback=MoeWebsite+"/tencentcallback")

    f = open('tx_rt', 'rb')
    auth.request_token = pickle.loads(f.read())
    f.close()
    access_token = auth.get_access_token(verifier)

    user_type = mc.get('user_type')
    mc.set('user_type', 'invalid')
    TencentData = WeiboAuth(access_token=access_token.key, access_token_secret=access_token.secret,
                            source="tencent", expires_in=13000000, user_type=user_type)
    TencentData.save()
    return HttpResponse("auth info saved")


def clean_auth(request):
    WeiboAuth.objects.all().delete()
    return HttpResponse("auth info has been cleaned")


def re_auth_sina(requset):
    try:
        WeiboAuth.objects.filter(source='sina').delete()
    except:
        pass
    return redirect(authSinaUrl())


def re_auth_tencent(requset):
    try:
        WeiboAuth.objects.filter(source='tencent').delete()
    except:
        pass
    return redirect(authTencentUrl())


def clean_cached_items(requset):
    cachedItems = WikiItems.objects.all()
    for item in cachedItems:
        if not item.was_add_recently():
            item.delete()

    return HttpResponse('ok')


def getWeiboAuthedApi(source, user_type):
    try:
        weiboData = WeiboAuth.objects.get(source=source, user_type=user_type)
    except Exception as e:
        log.info("no valid auth info for %s, %s found" % (source, user_type))
        raise e

    if source == 'sina':
        client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/sinacallback")
        client.set_access_token(weiboData.access_token, weiboData.expires_in)

        return client

    if source == 'tencent':
        auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret,
                                    callback=MoeWebsite+'/tencentcallback')
        auth.setToken(weiboData.access_token, weiboData.access_token_secret)
        api = qqweibo.API(auth, parser=qqweibo.ModelParser())
        return api
