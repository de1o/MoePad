import os
os.environ['DJANGO_SETTINGS_MODULE'] = "MoePad.settings"
from MoeWiki.models import RecentUpdateItems, MoePadConfig, WikiItems
from Auth.models import WeiboAuth
import datetime
from django.utils import timezone
import requests
import json
import time
import calendar
import urllib
from Auth import weibo
from Forbidden.models import ForbiddenWikiItems
import urllib2
from BeautifulSoup import BeautifulSoup
import logging
import logging.handlers
import traceback
from Auth.weibo import APIError

def loggerInit(logfile):
    logger = logging.getLogger(logfile)
    logger.setLevel(logging.DEBUG)
    fh = logging.handlers.RotatingFileHandler(logfile, maxBytes=10*1024*1024, backupCount=2)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

logger = loggerInit('sascript.log')


def mystrptime(str):
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

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

class MpConfig(object):
    def __init__(self):
        super(MpConfig, self).__init__()
    
    def getConfigFromDB(self):
        self.config = MoePadConfig.objects.all()[0]
        

class WeiboApi(object):
    def __init__(self, appkey, appsecret, callback, token, expires_in):
        super(WeiboApi, self).__init__()
        self.client = weibo.APIClient(appkey, appsecret, callback)
        self.client.set_access_token(token, expires_in)

    def send(self, text, url, img=None):
        short_link = self.client.short_url__shorten(url_long=url)
        shortUrl = short_link["urls"][0]["url_short"]
        text = ' '.join([text, shortUrl])

        if img:
            with open('tmp.jpg', 'rb') as fpic:
                r = self.client.statuses.upload.post(status=text, pic=fpic)
        else:
            r = self.client.statuses.update.post(status=text)


class UpdateItems(object):
    def __init__(self, config):
        super(UpdateItems, self).__init__()
        self.config = config
        self.rch = []
        self.ItemTobeSend = None
        
    def updateRoutine(self):
        try:
            self.delTooOldSentRecord()
            self.delTooOldAddedRecord()
            self.fetchNewItemGenerated(20)
            self.filterForbiddenItems()
            self.filterDuplicateItems()
            self.filterExistingItems()
            self.StoreRecentChangedItems()
        except:
            logger.info(traceback.format_exc())


    def delTooOldSentRecord(self):
        self.delRecentRecordSpecifiedHourAgo(self.config.sameItemInterval)

    def delTooOldAddedRecord(self):
        self.delRecentRecordSpecifiedHourAgo(self.config.generalRetainTime)

    def delRecentRecordSpecifiedHourAgo(self, hours):
        cutPoint = timezone.now() - datetime.timedelta(hours=hours)
        RecentUpdateItems.objects.filter(sentTime__lt=cutPoint).delete()

    def fetchNewItemGenerated(self, mins):
        url_t = "http://zh.moegirl.org/api.php?format=json&action=query&list=recentchanges&rcstart=%s&rcend=%s&rcdir=newer&rcnamespace=0"
        rcstart = calendar.timegm((timezone.now() - datetime.timedelta(minutes=mins)).utctimetuple())
        rcend = calendar.timegm(timezone.now().utctimetuple())
        url = url_t % (rcstart, rcend)
        r = requests.get(url)
        rjson = json.loads(r.text)
        self.rch =  rjson['query']['recentchanges']

    def filterForbiddenItems(self):
        self.forbiddenKeys = ForbiddenWikiItems.objects.all()
        
        cleanList = []
        for item in self.rch:
            if self.isItemContainsForbiddenKey(item['title']):
                continue
            else:
                cleanList.append(item)

        self.rch = cleanList

    def isItemContainsForbiddenKey(self, item):
        for fword in self.forbiddenKeys:
            if fword.title in item:
                return True

        return False

    def filterDuplicateItems(self):
        cleanList = []
        titleList = []
        for item in self.rch:
            if item['title'] not in titleList:
                cleanList.append(item)
                titleList.append(item['title'])

        self.rch = cleanList


    def filterExistingItems(self):
        self.loadExistedItems()
        self.rch = [item for item in self.rch if self.insertable(item)]

    def loadExistedItems(self):
        self.rcUpdateItems = RecentUpdateItems.objects.all()

    def StoreRecentChangedItems(self):
        map(self.storeValidItem, self.rch)

    def insertable(self, item):
        if self.rcUpdateItems.filter(title=item['title']):
            return False

        return True

    def storeValidItem(self, item):
        if item['type'] == 'new':
            itemState = RecentUpdateItems.VERIFYING_NEW
        else:
            itemState = RecentUpdateItems.EDITED
        print 'save'
        newItemRec = RecentUpdateItems(title=item['title'], itemState=itemState, changeTime=mystrptime(item['timestamp']))
        newItemRec.save()

    def sendRoutine(self):
        try:
            self.loadExistedItems()
            self.getItemTobeSend()
            print self.ItemTobeSend
            self.send()
        except APIError as e:
            if 'expired_token' in e:
                print "Token Expired"
                # TODO send reauth mail

            logger.info(traceback.format_exc())
        except:
            logger.info(traceback.format_exc())

    def getItemTobeSend(self):
        try:
            self.getVerifiedItem()
            return None
        except IndexError:
            print 'No verified New Item'

        try:
            self.getEditedItem()
        except IndexError:
            print 'No Edited New Item'
            return None

    def getVerifiedItem(self):
        verifiedItems = self.rcUpdateItems.filter(itemState=RecentUpdateItems.VERIFIED)
        try:
            self.ItemTobeSend = verifiedItems[0]
        except IndexError:
            pastDue = timezone.now() - datetime.timedelta(hours=24)
            autoVerifiedAfterCreate = self.rcUpdateItems.filter(itemState=RecentUpdateItems.VERIFYING_NEW, changeTime__lt=pastDue)
            self.ItemTobeSend = autoVerifiedAfterCreate[0]

    def getEditedItem(self):
        editedItems = self.rcUpdateItems.filter(itemState=RecentUpdateItems.EDITED).order_by('-changeTime')
        self.ItemTobeSend = editedItems[0]

    def send(self):
        if not self.ItemTobeSend:
            return None

        self.getWeiboApi()

        weiboTitle = self.ItemTobeSend.title
        weiboLink = "http://zh.moegirl.org/" + urllib.quote(weiboTitle.encode('utf-8'))

        self.weiboApi.send(weiboTitle, weiboLink, getImage(weiboLink))
        self.updateSentRecord()

    def updateSentRecord(self):
        self.rcUpdateItems.filter(title=self.ItemTobeSend.title).update(itemState=RecentUpdateItems.SENT, sentTime=timezone.now())

    def getWeiboApi(self):
        token = WeiboAuth.objects.get(source='sina', user_type='original')
        self.weiboApi = WeiboApi(self.config.SinaAppKey,
            self.config.sinaAppSecret,
            self.config.MoeWebsite+'/sinacallback',
            token.access_token,
            token.expires_in)

if __name__ == '__main__':
    config = MpConfig()
    config.getConfigFromDB()
    
    update = UpdateItems(config.config)    

    update.sendRoutine()
    # update.updateRoutine()