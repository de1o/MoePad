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


def sendToSina(newTweet, imgflag=True):
    try:
        client = getWeiboAuthedApi(source='sina', user_type='original')
    except:
        return 'no valid auth info for sina', None

    short_link = client.short_url__shorten(url_long=newTweet['link'])
    short_url = short_link["urls"][0]["url_short"]
    text = newTweet['text'] + " " + short_url
    if newTweet["img"] and imgflag:
        fpic = open('tmp.jpg', 'rb')
        r = client.statuses.upload.post(status=text, pic=fpic)
        fpic.close()
    else:
        r = client.statuses.update.post(status=text)
    log.info('[%s]sina update succ' % newTweet['text'])
    return 'succ', r.idstr


def sendToTencent(newTweet):
    try:
        api = getWeiboAuthedApi(source='tencent', user_type='original')
    except:
        return 'no valid auth info for tencent'

    text = newTweet['text'] + " " + newTweet['link']
    if newTweet['img']:
        fpic = open('tmp.jpg', 'rb')
        api.tweet.addpic(fpic, text, clientip='127.0.0.1')
        fpic.close()
    else:
        api.tweet.add(text, clientip='127.0.0.1')
    log.info('[%s]tencent update succ' % newTweet['text'])
    return 'succ'


def send(requset):
    newTweet = getNewTweet()
    if not newTweet:
        log.info('no new wiki item yet')
        return HttpResponse('no new tweet send!')

    fpic = None
    if newTweet['img']:
        fpic = open('tmp.jpg', 'wb')
        fpic.write(newTweet['img'])
        fpic.close()

    item_text = "[%s]" % newTweet['text']
    try:
        tencent_result = sendToTencent(newTweet)
    except Exception:
        log.info(item_text + traceback.format_exc())
        tencent_result = 'fail'

    try:
        sina_result, stid = sendToSina(newTweet)
        # retweet proc
        if stid:
            SinaRetweet(stid)
    except (HTTPError, APIError) as e:
        log.info(item_text + traceback.format_exc())
        sina_result, stid = sendToSina(newTweet, False)
        if stid:
            SinaRetweet(stid)
    except:
        log.info(item_text + traceback.format_exc())
        sina_result = 'fail'

    return HttpResponse('sina: %s %s, tencent %s' % (sina_result, stid, tencent_result))


def SinaRetweet(tid=None):
    if not tid:
        tid_provided = False
        tid = getNewSinaTid()
        if not tid:
            log.info("no new tweets for sina to retweet")
            return HttpResponse("no new tweets for sina to retweet")
    else:
        tid_provided = True
    client = getWeiboAuthedApi(source='sina', user_type='retweet')
    client.statuses.repost.post(id=int(tid))
    retweetData = AlreadlyRetweeted(tid=tid, source='sina', date=timezone.now())
    retweetData.save()
    log.info("Sina retweet succ %s" % tid)
    if not tid_provided:
        return HttpResponse("Sina retweet Succ")
    return None


def TencentRetweet():
    return HttpResponse("Tencent retweet Succ")


def retweet(requset, source):
    if source == 'sina':
        return SinaRetweet()
    elif source == 'tencent':
        return TencentRetweet()
    else:
        log.info('invalid retweet request source %s' % source)
        return HttpResponse('fail')


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
