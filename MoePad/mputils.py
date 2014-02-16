#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Sai
# @Date:   2014-02-12 23:13:59
# @Email:  email@example.com
# @Last modified by:   Sai
# @Last modified time: 2014-02-16 16:23:15
# 🎵 ミライナイト
import redis
import logging

rs = redis.Redis("localhost")
logger = logging.getLogger('moepad')


def sub_dict(somedict, somekeys, default=None):
    return dict([(k, somedict.get(k, default)) for k in somekeys])


def loggerInit(logfile):
    logger = logging.getLogger(logfile)
    logger.setLevel(logging.DEBUG)
    fh = logging.handlers.RotatingFileHandler(
        logfile, maxBytes=10*1024*1024, backupCount=2)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def mystrptime(str):
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)
