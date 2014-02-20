#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Sai
# @Date:   2014-02-13 22:16:44
# @Email:  email@example.com
# @Last modified by:   delo
# @Last modified time: 2014-02-17 22:01:20
from mputils import rs

MoePadConfKey = "MoePadConf"


class MpConfig(object):
    def __init__(self):
        super(MpConfig, self).__init__()

    def getConfig(self):
        # self.config = MoePadConfig.objects.all()[0]
        pass


class MpConfigRedisHandler(MpConfig):
    def __init__(self):
        super(MpConfigRedisHandler, self).__init__()
        self.getConfig()

    def getConfig(self):
        confdict = rs.hgetall(MoePadConfKey)
        for key in confdict:
            setattr(self, key, confdict[key])

MPConf = MpConfigRedisHandler()
