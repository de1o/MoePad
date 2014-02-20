#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: delo
# @Date:   2014-02-17 21:52:20
# @Email:  deloeating@gmail.com
# @Last modified by:   delo
# @Last modified time: 2014-02-17 22:28:43
import mpconfig
from mputils import rs
from pytest import fixture


@fixture
def confData(request):
    mpconfig.MoePadConfKey = "MoePadConfTest"
    rs.hmset(mpconfig.MoePadConfKey,
             {
                 "sameItemInterval": '24',
                 "Domain": "www.pythonik.com",
                 "SinaAppSecret": "c146e4d5772bf6a3363d9c804ed2c128",
                 "SinaAppKey": "255208104",
                 "TencentAppKey": "255208102",
                 "TencentAppSecret": "c146e4d5772bf6a3363d9c804ed2c129",
             })

    @request.addfinalizer
    def teardown():
        rs.delete(mpconfig.MoePadConfKey)

    return mpconfig.MpConfigRedisHandler()


def test_mpconfigRedisHandler(confData):
    assert confData.sameItemInterval == '24'
    assert confData.Domain == "www.pythonik.com"
    assert set(confData.__dict__.keys()) == set([
        "sameItemInterval",
        "Domain",
        "SinaAppKey",
        "SinaAppSecret",
        "TencentAppSecret",
        "TencentAppKey",
        ])
