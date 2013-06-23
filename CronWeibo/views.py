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

SinaAppKey = mpconfig.SinaAppKey
SinaAppSecret = mpconfig.SinaAppSecret
MoeWebsite = mpconfig.MoeWebsite


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
    return None


def sinacallback(request):
    code = request.GET['code']
    print code
    access_token, expires_in = authSina(code)
    return HttpResponse("auth info saved")


def clean_auth(request):
    WeiboAuth.objects.all().delete()
    return HttpResponse("auth info has been cleaned")


def loginSina(request):
    return redirect(authSinaUrl())


def loginTencent(requset):
    return redirect(authTencentUrl)


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
        f = open("tmp.jpg", "wb")
        f.write(newTweet["img"])
        f.close()
        f = open("tmp.jpg")
        client.statuses.upload.post(status=text, pic=f)
        f.close()
    else:
        client.statuses.update.post(status=text)


def send(requset):
    sina_client = weibo.APIClient(SinaAppKey, SinaAppSecret, MoeWebsite+"/callback")
    try:
        sinaData = WeiboAuth.objects.get(source="sina")
    except:
        return HttpResponse('no valid auth info found, please login first')

    sina_client.set_access_token(sinaData.access_token, sinaData.expires_in)

    # get tencent api here

    newTweet = getNewTweet()

    try:
        sendToSina(sina_client, newTweet)
        # sendToTencent(tencent_client, newTweet)
        return HttpResponse('send succ!')
    except:
        return HttpResponse('no new tweet send!')


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
