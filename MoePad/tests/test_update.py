#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: delo
# @Date:   2014-02-17 23:12:19
# @Email:  deloeating@gmail.com
# @Last modified by:   delo
# @Last modified time: 2014-02-18 21:27:22
import update


def test_getItemCategories():
    possible_categories = ['R-18', 'R18']
    real_categories = update.getItemCategories(u'Ahe颜')
    assert len(set(possible_categories).intersection(set(real_categories)))
