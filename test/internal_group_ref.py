#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigRoot, ConfigItem
from multiconf.envs import Env, EnvGroup

prod = Env('prod')
dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
g_dev = EnvGroup('g_dev', dev2st, dev2ct)

valid_envs = [g_dev, prod]

def conf(env):
    with ConfigRoot(env, valid_envs) as dc:
        dc.ms_suffixes(prod=[1, 2, 3, 4], g_dev=[1])
        print dc.ms_suffixes

        for ms_suffix in dc.ms_suffixes.value():
            with ConfigItem(True, id=ms_suffix-1, suffix=ms_suffix) as c:
                assert c.suffix().value() == ms_suffix

        return dc


def test(env, exp_ms_suffixes, exp_suffix):
    print '---- Loading Config: ' + repr(env) + ' -----'
    c = conf(env)
    print '---- Loaded -----'
    print '---- Printing -----'
    print 'c.ms_suffixes:', repr(c.ms_suffixes)
    assert c.ms_suffixes == exp_ms_suffixes
    print 'c.ConfigItems:', repr(c.ConfigItems)
    print 'c.ConfigItems[0]:', repr(c.ConfigItems[0])
    print 'c.ConfigItems[0].suffix:', repr(c.ConfigItems[0].suffix)
    assert c.ConfigItems[0].suffix == exp_suffix
    print '---- Printed -----'

test(dev2ct, [1], 1)
print
test(prod, [1, 2, 3, 4], 1)
