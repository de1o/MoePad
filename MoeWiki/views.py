import feedparser
from MoeWiki.models import WikiItems
from Forbidden.models import ForbiddenWikiItems
from BeautifulSoup import BeautifulSoup
import urllib2
import mpconfig

feedurl = mpconfig.feedurl


def parseFeed(feedurl):
    feeds = feedparser.parse(feedurl)
    return feeds


def findNewestItem(newFeeds):
    flag = 0
    recentItems = [item for item in WikiItems.objects.all() if item.was_add_recently()]
    forbiddenItems = [item.title for item in ForbiddenWikiItems.objects.all()]
    if not recentItems:
        return newFeeds[0]
    for newItem in newFeeds:
        if newItem['title'] in forbiddenItems:
            print 'Forbidden!'
            continue
        for recentItem in recentItems:
            if newItem['title'] == recentItem.title:
                flag = 1
                break
        if flag:
            flag = 0
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
    try:
        link = feedToBeSend['link'][:feedToBeSend['link'].index('&')]
    except:
        link = feedToBeSend['link']
    return {'text': text, 'img': img, 'link': link}


def getNewTweet():
    return getNewWikiItem()
