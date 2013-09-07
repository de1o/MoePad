from apscheduler.scheduler import Scheduler
import urllib2
from myscript import MpConfig, UpdateItems


def check_update():
    print 'update'
    config = MpConfig()
    config.getConfigFromDB()
    update = UpdateItems(config.config)
    update.updateRoutine()

def send():
    print 'send'
    config = MpConfig()
    config.getConfigFromDB()
    update = UpdateItems(config.config)
    update.sendRoutine()

# need server timezone should be GMT+8
def day_send():
    day_send_sched = Scheduler()
    day_send_sched.daemonic = False
    day_send_sched.add_cron_job(send, hour='7-23', minute='10,30,50', second=0)
    day_send_sched.start()

def night_send():
    night_send_sched = Scheduler()
    night_send_sched.daemonic = False
    night_send_sched.add_cron_job(send, hour='0-6', minute=10, second=0)
    night_send_sched.start()

def updateNewItem():
    update_sched = Scheduler()
    update_sched.daemonic = False
    update_sched.add_cron_job(check_update, hour='0-23', minute='8,28,48', second=0)
    update_sched.start()


if __name__ == '__main__':
    day_send()
    night_send()
    updateNewItem()
    print 'scheduler tasks started'
