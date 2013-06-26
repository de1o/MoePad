from apscheduler.scheduler import Scheduler
import urllib2
import mpconfig

website = mpconfig.MoeWebsite
check_update_url = website + "/send/"
clean_cache_url = website + "/clean_cached_items/"
reauth_url = website + "/send_reauth_mail/"


def check_update():
    print 'update'
    urllib2.urlopen(check_update_url)


def clean_cached_items():
    urllib2.urlopen(clean_cache_url)


def send_reauth_email():
    urllib2.urlopen(reauth_url)

# need server timezone should be GMT+8
day_update_sched = Scheduler()
day_update_sched.daemonic = False
day_update_sched.add_cron_job(check_update, hour='7-23', minute='10,30,50', second=0)
day_update_sched.start()

night_update_sched = Scheduler()
night_update_sched.daemonic = False
night_update_sched.add_cron_job(check_update, hour='0-6', minute=10, second=0)
night_update_sched.start()

clean_cached_sched = Scheduler()
clean_cached_sched.daemonic = False
clean_cached_sched.add_interval_job(clean_cached_items, days=1)
clean_cached_sched.start()

send_reauth_sched = Scheduler()
send_reauth_sched.daemonic = False
send_reauth_sched.add_interval_job(send_reauth_email, weeks=1)
send_reauth_sched.start()

print 'scheduler tasks started'
