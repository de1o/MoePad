#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Sai
# @Date:   2014-02-12 23:13:59
# @Email:  email@example.com
# @Last modified by:   delo
# @Last modified time: 2014-02-19 23:15:25
# 🎵 ミライナイト
import redis
import logging
import logging.handlers
from datetime import datetime
import pytz
import os
import os.path as p

rs = redis.Redis("localhost")
logger = logging.getLogger('moepad')


def sub_dict(somedict, somekeys, default=None):
    return dict([(k, somedict.get(k, default)) for k in somekeys])


def loggerInit(logfile):
    logger = logging.getLogger(logfile)
    logger.setLevel(logging.DEBUG)
    try:
        fh = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=10*1024*1024, backupCount=2)
    except IOError:
        os.makedirs(p.dirname(logfile))
        fh = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=10*1024*1024, backupCount=2)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def utcnow():
    tz = pytz.timezone('UTC')
    return datetime.now(tz)
