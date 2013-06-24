# -*- coding:utf-8 -*-
from CronWeibo.models import WeiboAuth
from django.http import HttpResponse
from django.shortcuts import *
from MoeWiki.views import getNewTweet
from email.mime.text import MIMEText
from MoeWiki.models import WikiItems
import mpconfig
import weibo
import smtplib
import time
import qqweibo
import pickle

SinaAppKey = mpconfig.SinaAppKey
SinaAppSecret = mpconfig.SinaAppSecret
TencentAppKey = mpconfig.TencentAppKey
TencentAppSecret = mpconfig.TencentAppSecret
MoeWebsite = mpconfig.MoeWebsite
if not MoeWebsite.startswith("http"):
    raise Exception


def authSina(code):
    client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/callback")
    r = client.request_access_token(code)

    sinaData = WeiboAuth(access_token=r.access_token, expires_in=r.expires_in, source="sina")
    sinaData.save()
    return r.access_token, r.expires_in


def authSinaUrl():
    client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/callback")
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
    print code
    access_token, expires_in = authSina(code)
    return HttpResponse("auth info saved")


def tencentcallback(request):
    verifier = request.GET['oauth_verifier']
    auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret, callback=MoeWebsite+"/tencentcallback")

    f = open('tx_rt', 'rb')
    auth.request_token = pickle.loads(f.read())
    f.close()
    access_token = auth.get_access_token(verifier)

    TencentData = WeiboAuth(access_token=access_token.key, access_token_secret=access_token.secret, source="tencent", expires_in=13000000)
    TencentData.save()
    return HttpResponse("auth info saved")


def clean_auth(request):
    WeiboAuth.objects.all().delete()
    return HttpResponse("auth info has been cleaned")


def loginSina(request):
    return redirect(authSinaUrl())


def loginTencent(requset):
    return redirect(authTencentUrl())


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


def send_reauth_mail(requset):
    mailbody = 'hello, please reauthorize account. sina click %s ,tencent click %s' % (MoeWebsite + '/re_auth_sina', MoeWebsite + '/re_auth_tencent')
    mail_from = mpconfig.mail_from
    mail_to = mpconfig.mail_to
    msg = MIMEText(mailbody)
    msg['Subject'] = 'Reauthorize moegirl gengxinji'
    msg['From'] = mail_from
    msg['To'] = mail_to
    msg['date'] = time.strftime('%a, %d %b %Y %H:%M:%S %z')

    smtp = smtplib.SMTP()
    smtp.connect(mpconfig.smtpserver)
    smtp.login(mpconfig.mail_user, mpconfig.mail_passwd)
    smtp.sendmail(mail_from, mail_to, msg.as_string())
    smtp.quit()

    return HttpResponse('ok')


def clean_cached_items(requset):
    cachedItems = WikiItems.objects.all()
    for item in cachedItems:
        if not item.was_add_recently():
            item.delete()

    return HttpResponse('ok')


def sendToSina(client, newTweet):
    short_link = client.short_url__shorten(url_long=newTweet['link'])
    short_url = short_link["urls"][0]["url_short"]
    text = newTweet['text'] + " " + short_url
    if newTweet["img"]:
        fpic = open('tmp.jpg', 'rb')
        client.statuses.upload.post(status=text, pic=fpic)
        fpic.close()
    else:
        client.statuses.update.post(status=text)


def sendToTencent(api, newTweet):
    text = newTweet['text'] + " " + newTweet['link']
    if newTweet['img']:
        fpic = open('tmp.jpg', 'rb')
        api.tweet.addpic(fpic, text, clientip='127.0.0.1')
        fpic.close()
    else:
        api.tweet.add(text, clientip='127.0.0.1')


def send(requset):
    newTweet = getNewTweet()
    if not newTweet:
        return HttpResponse('no new tweet send!')

    fpic = None
    if newTweet['img']:
        fpic = open('tmp.jpg', 'wb')
        fpic.write(newTweet['img'])
        fpic.close()

    # get sina api
    sina_client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/callback")
    try:
        sinaData = WeiboAuth.objects.get(source="sina")
    except:
        return HttpResponse('no valid auth info for sina found, please login first')

    sina_client.set_access_token(sinaData.access_token, sinaData.expires_in)

    # get tencent api here
    auth = qqweibo.OAuthHandler(TencentAppKey, TencentAppSecret, callback=MoeWebsite+'/tencentcallback')
    try:
        TencentData = WeiboAuth.objects.get(source="tencent")
    except:
        return HttpResponse('no valid auth info for tencent found, please login first')
    auth.setToken(TencentData.access_token, TencentData.access_token_secret)
    t_api = qqweibo.API(auth, parser=qqweibo.ModelParser())

    sendToSina(sina_client, newTweet)
    sendToTencent(t_api, newTweet)
    return HttpResponse('send succ!')


def index(requset):
    html = """
<!DOCTYPE HTML>
<html>
<head>
<title>MoePad</title>
</head>
<a href="%s" target="_blank">清除认证信息</a>
<a href="%s" target="_blank">新浪认证</a>
<a href="%s" target="_blank">腾讯认证</a>


</html>
""" % (MoeWebsite+'/clean_auth', MoeWebsite+'/loginSina', MoeWebsite+'/loginTencent')
    return HttpResponse(html)
