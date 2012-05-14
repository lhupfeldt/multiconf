#!/usr/bin/python

# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf.multiconf import ConfigRoot, ConfigItem
from multiconf.multiconf import Env, EnvGroup

prod = Env('prod')
dev2ct = Env('dev2CT')
dev2st = Env('dev2ST')
g_dev = EnvGroup('g_dev', dev2st, dev2ct)

valid_envs = [g_dev, prod]

def config(env):
    with ConfigRoot(env, valid_envs) as conf:
        conf.a(prod="hello", g_dev="hi")
        print 'conf.a:', conf.a

        with ConfigItem(id=0, repeat=True) as c:
            c.a(prod="hello nested", g_dev="hi nested")

        return conf

def test(env):
    conf = config(env)

    print "----", env, "----"
    print 'conf.a', repr(conf.a)
    print 'conf.ConfigItems[0].a', repr(conf.ConfigItems[0].a)
    print

    print "Full config:\n", conf

test(prod)
test(dev2ct)
