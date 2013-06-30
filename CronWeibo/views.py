# -*- coding:utf-8 -*-
from django.http import HttpResponse, Http404
from django.shortcuts import *
from MoeWiki.views import getNewTweet, getNewSinaTid
from MoeWiki.models import AlreadlyRetweeted
from email.mime.text import MIMEText
import mpconfig
import smtplib
import time
import traceback
from urllib2 import HTTPError
from Auth.weibo import APIError
from Auth.views import getWeiboAuthedApi, authSinaUrl, authTencentUrl
from mpconfig import *
import logging
from django.utils import timezone


log = logging.getLogger('moepad')


def logTraceInfo(prefix):
    log.info(("[%s]" % prefix) + traceback.format_exc())


def save_usertype(user_type):
    if user_type in ['original', 'retweet']:
        mc.set('user_type', user_type)
    else:
        log.info("invalid user_type")
        raise Exception


def loginSina(request, user_type):
    try:
        save_usertype(user_type)
    except:
        raise Http404
    return redirect(authSinaUrl())


def loginTencent(requset, user_type):
    try:
        save_usertype(user_type)
    except:
        raise Http404
    return redirect(authTencentUrl())


def send_reauth_mail(requset):
    mailbody = 'hello, please reauthorize account. sina click %s ,tencent click %s' % (MoeWebsite + '/re_auth_sina',
                                                                                       MoeWebsite + '/re_auth_tencent')
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


def sendToSina(newTweet):
    try:
        client = getWeiboAuthedApi(source='sina', user_type='original')
    except:
        logTraceInfo("no valid auth info for sina")
        return None

    try:
        short_link = client.short_url__shorten(url_long=newTweet['link'])
    except:
        logTraceInfo(newTweet['text'])
        return None

    short_url = short_link["urls"][0]["url_short"]
    text = newTweet['text'] + " " + short_url
    try:
        if newTweet["img"]:
            fpic = open('tmp.jpg', 'rb')
            r = client.statuses.upload.post(status=text, pic=fpic)
            fpic.close()
        else:
            r = client.statuses.update.post(status=text)
    except (HTTPError, APIError) as e:
        try:
            logTraceInfo(newTweet['text'])
            r = client.statuses.update.post(status=text)
        except:
            logTraceInfo(newTweet['text'])
            return None
    except:
        logTraceInfo(newTweet['text'])
        return None
    log.info('[%s]sina update succ' % newTweet['text'])
    return r


def sendToTencent(newTweet):
    try:
        api = getWeiboAuthedApi(source='tencent', user_type='original')
    except:
        return 'no valid auth info for tencent'

    text = newTweet['text'] + " " + newTweet['link']
    try:
        if newTweet['img']:
            fpic = open('tmp.jpg', 'rb')
            api.tweet.addpic(fpic, text, clientip='127.0.0.1')
            fpic.close()
        else:
            api.tweet.add(text, clientip='127.0.0.1')
    except:
        log.info(("[%s]" % newTweet['text']) + traceback.format_exc())
        return 'fail'
    log.info('[%s]tencent update succ' % newTweet['text'])
    return 'succ'


def send(requset):
    newTweet = getNewTweet()
    if not newTweet:
        log.info('no new wiki item yet')
        return HttpResponse('no new tweet send!')

    rt = sendToTencent(newTweet)
    rs = sendToSina(newTweet)

    return HttpResponse('sina: %s %s, tencent %s' % ('succ' if rs else 'fail', rs.idstr if rs else 'None', rt))


def sendThenRetweet(requset):
    newTweet = getNewTweet()
    if not newTweet:
        log.info('no new wiki item yet')
        return HttpResponse('no new tweet send!')

    result_t = sendToTencent(newTweet)
    result_s = sendToSina(newTweet)

    if result_s:
        rt_result_s = SinaRetweet(tid=result_s.idstr)

    return HttpResponse('sina send %s retweet %s, tencent %s' % ('succ' if result_s else 'fail', 'succ' if rt_result_s else 'fail', result_t))


def SinaRetweet(tid):
    try:
        client = getWeiboAuthedApi(source='sina', user_type='retweet')
    except:
        logTraceInfo(tid)
        return None
    try:
        r = client.statuses.repost.post(id=int(tid), status="萌百更新")
    except:
        logTraceInfo(tid)
        return None
    log.info("Sina retweet succ %s" % tid)
    return r


def index(requset):
    html = """
<!DOCTYPE HTML>
<html>
<head>
<title>MoePad</title>
</head>
<a href="%s" target="_blank">清除认证信息</a><br/>
<a href="%s" target="_blank">新浪发送帐户认证</a><br/>
<a href="%s" target="_blank">新浪转发帐户认证</a><br/>
<a href="%s" target="_blank">腾讯发送帐户认证</a><br/>
<!--<a href="%s" target="_blank">腾讯转发帐户认证</a><br/>-->


</html>
""" % (MoeWebsite+'/clean_auth/',
        MoeWebsite+'/loginSina/original/',
        MoeWebsite+'/loginSina/retweet/',
        MoeWebsite+'/loginTencent/original/',
        MoeWebsite+'/loginTencent/retweet/')
    return HttpResponse(html)
