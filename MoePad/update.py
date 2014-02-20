# -*- coding: utf-8 -*-
# import os
# os.environ['DJANGO_SETTINGS_MODULE'] = "MoeDj.settings"
import datetime
import requests
import json
import time
import calendar
import urllib
import urllib2
import logging
import logging.handlers
import traceback
from BeautifulSoup import BeautifulSoup

from weibowrapper import WeiboApi, WeiboAuthInfoRedis
from weibo import APIError
from mputils import rs, loggerInit, utcnow
from mpconf import MPConf


logger = loggerInit('MoePad.log')
VERIFYING_PREFIX = 'ToBeSendVerifying'
VERIFIED_PREFIX = 'ToBeSendVerified'
EDITED_PREFIX = 'ToBeSendEdited'
SENT_PREFIX = 'SentItem'
ORDERED_SET = 'OrderedByExpireTimeSet'
# the real expire time set in redis key should be a bit longer
# than the score (which represent items' expiry time) in zset, so the
# verifying items can be moved to verified item list before it's infomation
# disappeared by lifetime expired
VERIFYING_EXPIRE = 25*3600  # 24 hours
VERIFYING_ZSET_SCORE = 24*3600
VERIFIED_EXPIRE = 24*3600   # 24 hours
EDITED_EXPIRE = 24*3600     # 24 hours
# according to user configuration
SENT_EXPIRE = int(MPConf.sameItemInterval)*3600
queryCategoryUrl = "http://zh.moegirl.org/api.php?format=json&action=query&prop=categories&titles=%s"


def getItemCategories(title):
    url = queryCategoryUrl % urllib.quote(title.encode('utf-8'))
    r = requests.get(url)
    rjson = json.loads(r.text)
    pages = rjson['query']['pages']
    key = pages.keys()[0]
    categories = pages[key]['categories']
    categories = [c['title'].strip('Category:') for c in categories]
    return categories


def getImage(link):
    try:
        c = urllib2.urlopen(link)
    except:
        return None
    f = c.read()
    c.close()

    soup = BeautifulSoup(f)
    content = soup.find("div", {"id": "bodyContent"})
    img = None
    for tag in content.findAll('img'):
        try:
            if ((int(tag["width"]) < 100) or (int(tag["width"]) > 800)):
                continue
        except:
            continue
        try:
            if ((int(tag["height"]) < 100) or (int(tag["height"]) > 800)):
                continue
        except:
            continue
        img = tag
        break

    result = False
    if img:
        src = str(img["src"])
        if src.startswith("//1-ps.google"):
            src = img["pagespeed_lazy_src"]
        elif src.startswith("//"):
            src = "http:" + src

        image_remote = urllib2.urlopen(src)
        if image_remote.getcode() != 200:
            return None
        image_content = image_remote.read()
        with open("tmp.jpg", 'wb') as fpic:
            fpic.write(image_content)
        result = True
        # resize img ?
    return result


def filterForbiddenItems(that):
    forbiddenKeys = rs.lrange("ForbiddenItem", 0, -1)
    for key in forbiddenKeys:
        if key in that['title']:
            return False
    return True


def filterExistedItems(that):
    unsendKeys = rs.keys(VERIFIED_PREFIX) + \
        rs.keys(VERIFYING_PREFIX) + \
        rs.keys(EDITED_PREFIX) + \
        rs.keys(SENT_PREFIX)

    for key in unsendKeys:
        if that['title'] == rs.hget(key, "title"):
            return False
    return True


class UpdateItems(object):

    filters = [
        filterForbiddenItems,
        filterExistedItems, ]

    def __init__(self):
        super(UpdateItems, self).__init__()
        self.rch = []
        self.ItemTobeSend = None

    def updateRoutine(self):
        try:
            self.fetchNewItemGenerated(120)
            self.cleanExpiredItem()
            self.filter_valid()
            self.StoreRecentChangedItems()
        except:
            logger.info(traceback.format_exc())

    def fetchNewItemGenerated(self, mins):
        url_t = "http://zh.moegirl.org/api.php?format=json&action=query&list=recentchanges&rcstart=%s&rcend=%s&rcdir=newer&rcnamespace=0&rctoponly&rctype=edit|new"
        rcstart = calendar.timegm((utcnow() - datetime.timedelta(
            minutes=mins)).utctimetuple())
        rcend = calendar.timegm(utcnow().utctimetuple())
        url = url_t % (rcstart, rcend)
        print url
        r = requests.get(url)
        rjson = json.loads(r.text)
        self.rch = rjson['query']['recentchanges']
        logger.debug(self.rch)

    # if item is in verifying pool and is about to expire, delete from zset and
    # move from verifying pool to verified pool, then add a verified item in
    # zset.
    # if item is not in verifying pool, just delete from zset.
    def cleanExpiredItem(self):
        expiringItems = rs.zrange(ORDERED_SET, 0, -1)
        verifyingItems = filter(lambda x: x.startswith(VERIFYING_PREFIX),
                                expiringItems)
        for verifyingKey in verifyingItems:
            print rs.zscore(ORDERED_SET, verifyingKey) - time.time(), '---'
            if rs.zscore(ORDERED_SET, verifyingKey) < time.time():
                # if a verifying key in zset, if it is expired by score,
                # first check if this key exist in verifying pool,
                # if not, just delete from zset
                rs.zrem(ORDERED_SET, verifyingKey)
                data = rs.hgetall(verifyingKey)
                if not data:
                    break
                title = verifyingKey.strip(VERIFYING_PREFIX)
                verifiedKey = VERIFIED_PREFIX + title
                rs.zadd(ORDERED_SET, VERIFIED_PREFIX+title,
                        time.time()+VERIFIED_EXPIRE)
                rs.hmset(verifiedKey, data)
                rs.expire(verifiedKey, VERIFIED_EXPIRE)
                rs.delete(verifyingKey)

        notVerifyingItem = filter(
            lambda x: not x.startswith(VERIFYING_PREFIX), expiringItems)
        for item in notVerifyingItem:
            if rs.zscore(ORDERED_SET, item) < time.time():
                rs.zrem(ORDERED_SET, item)

    def filter_valid(self):
        for filterfunc in self.filters:
            self.rch = filter(filterfunc, self.rch)

    def StoreRecentChangedItems(self):
        for item in self.rch:
            if item['type'] == 'new':
                itemKey = VERIFYING_PREFIX + item['title']
                expire_time = VERIFYING_EXPIRE
                zset_score = VERIFYING_ZSET_SCORE + time.time()
            else:
                itemKey = EDITED_PREFIX + item['title']
                expire_time = VERIFIED_EXPIRE
                zset_score = VERIFIED_EXPIRE + time.time()
            rs.hmset(itemKey, item)
            rs.expire(itemKey, expire_time)
            rs.zadd(ORDERED_SET, itemKey, zset_score)

    def sendRoutine(self):
        self.getItemTobeSend()
        if not self.ItemTobeSend:
            return None
        try:
            self.send()
            logger.info("Sending: "+self.ItemTobeSend['title']+" Succ")
            self.updateSentRecord()
        except APIError as e:
            if 'expired_token' in e:
                print "Token Expired"
                # TODO send reauth mail
            logger.info(traceback.format_exc())
        except:
            logger.info(traceback.format_exc())

    def getItemTobeSend(self):
        ItemTobeSendTitle = None
        expiringItems = rs.zrange(ORDERED_SET, 0, -1)
        verifiedItems = filter(lambda x: x.startswith(VERIFIED_PREFIX),
                               expiringItems)
        print expiringItems
        print verifiedItems
        if verifiedItems:
            ItemTobeSendTitle = verifiedItems.pop(0)
        if not ItemTobeSendTitle:
            logger.info('No verified New Item')
            editedItems = filter(lambda x: x.startswith(EDITED_PREFIX),
                                 expiringItems)
            if editedItems:
                ItemTobeSendTitle = editedItems.pop(0)
        if not ItemTobeSendTitle:
            logger.info('No Edited New Item')
            self.ItemTobeSend = None
            self.ItemTobeSendTitle = None
            return None

        self.ItemTobeSend = rs.hgetall(ItemTobeSendTitle)
        self.ItemTobeSendTitle = ItemTobeSendTitle

    def send(self):
        if not self.ItemTobeSend:
            return None

        self.getWeiboApi()

        weiboTitle = self.ItemTobeSend['title']
        weiboLink = "http://zh.moegirl.org/" + \
                    urllib.quote(weiboTitle)

        self.weiboApi.send(weiboTitle.decode('utf-8'),
                           weiboLink, getImage(weiboLink))

    def updateSentRecord(self):
        key = SENT_PREFIX + self.ItemTobeSend['title']
        rs.hmset(key, self.ItemTobeSend)
        rs.expire(key, SENT_EXPIRE)
        rs.delete(self.ItemTobeSendTitle)

        # remove original item from zset and re-add into zset as sent state
        rs.zrem(ORDERED_SET, self.ItemTobeSendTitle)
        rs.zadd(ORDERED_SET, SENT_PREFIX+self.ItemTobeSend['title'],
                SENT_EXPIRE+time.time())

    def getWeiboApi(self):
        AuthInfo = WeiboAuthInfoRedis("original")
        token = rs.hgetall("WeiboAuth"+"original")
        self.weiboApi = WeiboApi(
            MPConf.SinaAppKey,
            MPConf.SinaAppSecret,
            MPConf.Domain+'/sinacallback',
            token['access_token'],
            token['expires_in'])

if __name__ == '__main__':
    update = UpdateItems()
    update.sendRoutine()
    # update.updateRoutine()
