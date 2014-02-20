#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: delo
# @Date:   2014-02-17 21:36:42
# @Email:  deloeating@gmail.com
# @Last modified by:   delo
# @Last modified time: 2014-02-18 00:56:00
import logging
import redis
from mputils import sub_dict, loggerInit, rs, logger


def test_subdict():
    a = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
    keys = ['k1', 'k3']
    assert sub_dict(a, keys) == {'k1': 'v1', 'k3': 'v3'}


def test_loggerInit():
    tlogger = loggerInit("test.log")
    assert isinstance(tlogger, logging.Logger)
