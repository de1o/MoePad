# -*- coding: utf-8 -*-
import feedparser
from MoeWiki.models import WikiItems, AlreadlyRetweeted
from Forbidden.models import ForbiddenWikiItems
from Auth.models import WeiboAuth
from BeautifulSoup import BeautifulSoup
from django.utils import timezone
import datetime
import urllib2
import mpconfig
import urllib
from Auth.views import getWeiboAuthedApi
import traceback
import logging

feedurl = mpconfig.feedurl
log = logging.getLogger('moepad')


def parseFeed(feedurl):
    feeds = feedparser.parse(feedurl)
    return feeds


def mystrptime(str):
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ")


def findNewestItem(newFeeds):
    recentItems = [item.title for item in WikiItems.objects.all() if item.was_add_recently()]
    forbiddenItems = [item.title for item in ForbiddenWikiItems.objects.all()]
    # remove tzinfo to convert into tz naive time
    recent_time_limit = (timezone.now().astimezone(timezone.utc).replace(tzinfo=None) - datetime.timedelta(hours=12))
    newFeeds = [feed for feed in newFeeds if (mystrptime(feed['date']) >= recent_time_limit)]
    if not recentItems:
        return newFeeds[0]
    for newItem in newFeeds:
        if newItem['title'] in forbiddenItems:
            continue
        if newItem['title'] in recentItems:
            continue
        else:
            return newItem
    return None


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

    image_content = None
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
        # resize img ?
    return image_content


def getNewWikiItem():
    newFeeds = parseFeed(feedurl)["items"]
    feedToBeSend = findNewestItem(newFeeds)
    if not feedToBeSend:
        return None

    WikiItemData = WikiItems(title=feedToBeSend["title"], link=feedToBeSend["link"], date=feedToBeSend["date"])
    WikiItemData.save()
    img = getImage(feedToBeSend["link"])
    text = feedToBeSend['title']
    link = "http://zh.moegirl.org/" + urllib.quote(feedToBeSend['title'].encode('utf-8'))
    return {'text': text, 'img': img, 'link': link}


def getNewTweet():
    return getNewWikiItem()


def getNewSinaTid():
    original_user = WeiboAuth.objects.get(source='sina', user_type='original')
    uid = original_user.uid
    client = getWeiboAuthedApi(source='sina', user_type='original')
    r = client.statuses.user_timeline.ids.get(uid=uid)
    newestId = r.statuses[0]  # string
    try:
        RecentSinaRetweets = [item.tid for item in AlreadlyRetweeted.objects.filter(source='sina') if item.was_add_recently()]
    except:
        log.info(traceback.format_exc())
        return newestId

    if newestId not in RecentSinaRetweets:
        return newestId
    return None
