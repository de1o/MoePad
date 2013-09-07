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

def getMoeWebSite():
    # a = MoePadConfig.objects.all()[0]
    return MoePadConfig.objects.all()[0].MoeWebsite


log = logging.getLogger('moepad')
def getSinaAppInfo():
    info = MoePadConfig.objects.all()[0]
    return info.SinaAppKey, info.sinaAppSecret

def authSina(code):
    SinaAppKey, SinaAppSecret = getSinaAppInfo()
    MoeWebsite = getMoeWebSite()
    client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/sinacallback")
    r = client.request_access_token(code)

    client.set_access_token(r.access_token, r.expires_in)
    ruid = client.account.get_uid.get()
    sinaData = WeiboAuth(access_token=r.access_token, expires_in=r.expires_in, source="sina",
                         user_type='original', uid=ruid.uid)
    sinaData.save()
    return r.access_token, r.expires_in


def authSinaUrl():
    SinaAppKey, SinaAppSecret = getSinaAppInfo()
    MoeWebsite = getMoeWebSite()
    client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/sinacallback")
    return client.get_authorize_url()


def authTencentUrl():
    MoeWebsite = getMoeWebSite()
    auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret, callback=MoeWebsite+"/tencentcallback")
    url = auth.get_authorization_url()
    f = open('tx_rt', 'wb')
    f.write(pickle.dumps(auth.request_token))
    f.close()
    return url

@login_required
def sinacallback(request):
    code = request.GET['code']
    access_token, expires_in = authSina(code)
    c = {"information": "auth info saved"}
    return render_to_response("info.html", c)

@login_required
def tencentcallback(request):
    verifier = request.GET['oauth_verifier']
    MoeWebsite = getMoeWebSite()
    auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret, callback=MoeWebsite+"/tencentcallback")

    f = open('tx_rt', 'rb')
    auth.request_token = pickle.loads(f.read())
    f.close()
    access_token = auth.get_access_token(verifier)

    TencentData = WeiboAuth(access_token=access_token.key, access_token_secret=access_token.secret,
                            source="tencent", expires_in=13000000, user_type=user_type)
    TencentData.save()

    c = {"information": "auth info saved"}
    return render_to_response("info.html", c)

@login_required
def clean_auth(request):
    WeiboAuth.objects.all().delete()
    c = {"information": "auth info has been cleaned"}
    # print 'hello'
    return render_to_response("info.html", c)

@login_required
def re_auth_sina(requset):
    try:
        WeiboAuth.objects.filter(source='sina').delete()
    except:
        pass
    return redirect(authSinaUrl())

@login_required
def re_auth_tencent(requset):
    try:
        WeiboAuth.objects.filter(source='tencent').delete()
    except:
        pass
    return redirect(authTencentUrl())

@login_required
def clean_cached_items(requset):
    cachedItems = WikiItems.objects.all()
    for item in cachedItems:
        if not item.was_add_recently():
            item.delete()

    c = {"information": "ok"}
    return render_to_response("info.html", c)


def getWeiboAuthedApi(source, user_type):
    MoeWebsite = getMoeWebSite()
    try:
        weiboData = WeiboAuth.objects.get(source=source, user_type=user_type)
    except Exception as e:
        log.info("no valid auth info for %s, %s found" % (source, user_type))
        raise e

    if source == 'sina':
        SinaAppKey, SinaAppSecret = getSinaAppInfo()
        client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/sinacallback")
        client.set_access_token(weiboData.access_token, weiboData.expires_in)

        return client

    if source == 'tencent':
        auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret,
                                    callback=MoeWebsite+'/tencentcallback')
        auth.setToken(weiboData.access_token, weiboData.access_token_secret)
        api = qqweibo.API(auth, parser=qqweibo.ModelParser())
        return api


@login_required
def loginSina(request, user_type):
    return redirect(authSinaUrl())
