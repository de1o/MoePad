from django.db import models
import datetime
from django.utils import timezone


class WikiItems(models.Model):
    title = models.CharField(max_length=100)
    link = models.CharField(max_length=256)
    date = models.DateTimeField()

    def __unicode__(self):
        return self.title

    def was_add_recently(self):
        return self.date >= timezone.now() - datetime.timedelta(hours=12)


class AlreadlyRetweeted(models.Model):
    tid = models.CharField(max_length=32)
    source = models.CharField(max_length=20)
    date = models.DateTimeField()

    def __unicode__(self):
        return self.tid

    def was_add_recently(self):
        return self.date >= timezone.now() - datetime.timedelta(hours=2)
