#!/usr/bin/python

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import cProfile

heap_check = sys.version_info.major < 3 and sys.argv[1] == 'mem'
if heap_check:
    from guppy import hpy
    hp = hpy()

import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigRoot, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory

ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children_init, children_default, children_env, children_mc_init')
class root(ConfigRoot):
    pass


@named_as('children_init')
class rchild_init(RepeatableConfigItem):
    def __init__(self, name, aa, bb, xx, yy):
        super(rchild_init, self).__init__(mc_key=name)
        self.name = name
        self.aa = aa
        self.bb = bb
        self.xx = xx
        self.yy = yy


@named_as('children_mc_init')
class rchild_mc_init(RepeatableConfigItem):
    def __init__(self, name, xx):
        super(rchild_mc_init, self).__init__(mc_key=name)
        self.name = name
        self.xx = xx

    def mc_init(self):
        super(rchild_mc_init, self).mc_init()
        self.override('xx', 17)
        self.override('yy', 18)
        self.override('zz', 19)


@named_as('children_default')
class rchild_default(RepeatableConfigItem):
    def __init__(self, name, aa):
        super(rchild_default, self).__init__(mc_key=name)
        self.name = name
        self.aa = aa


@named_as('children_env')
@nested_repeatables('children_init, children_default, children_env, children_mc_init')
class rchild_env(RepeatableConfigItem):
    def __init__(self, name):
        super(rchild_env, self).__init__(mc_key=name)
        self.name = name


def perf1():
    first_range = 2000
    second_range = 2000
    third_range = 2000

    with root(prod, ef) as cr:
        for ii in range(0, first_range):
            rchild_init(name=repr(ii), aa=1, bb=1, xx="hello", yy="hi")

        for ii in range(0, second_range):
            with rchild_default(name=repr(ii), aa=4) as ci:
                ci.setattr('a' + repr(ii), default=2)

        for ii in range(0, third_range):
            with rchild_env(name=repr(ii)) as ci:
                ci.setattr('aa' + repr(ii), dev1=7, dev2=8, tst=9, pp=18, prod=5)
                ci.setattr('bb' + repr(ii), g_dev=8, tst=9, pp=19, prod=3)
                ci.setattr('x' + repr(ii), g_dev=8, tst=9, pp=19, prod=3)
                ci.setattr('y' + repr(ii), g_dev=8, tst=9, pp=19, prod=3)
                ci.setattr('z' + repr(ii), g_dev=8, tst=9, pp=19, prod=3)

                with rchild_env(name='a' + repr(ii)) as ci:
                    ci.setattr('cc' + repr(ii), dev1=7, dev2=8, tst=9, pp=18, prod=5)
                    ci.setattr('dd' + repr(ii), g_dev=8, tst=9, pp=19, prod=3)

                    for jj in range(0, 10):
                        with rchild_default(name='ee' + repr(ii) + '_' + repr(jj), aa=4) as ci:
                            ci.setattr('ff' + repr(ii) + '_' + repr(jj), default=2, pp=3, prod=4)

                        with rchild_mc_init(name='gg' + repr(ii) + '_' + repr(jj), xx=7) as ci:
                            ci.setattr('hh' + repr(ii) + '_' + repr(jj), default=2, pp=3, prod=4)
                            ci.setattr('ii' + repr(ii) + '_' + repr(jj), default=2, pp=3, prod=4)

                    with rchild_default(name='jj' + repr(ii), aa="hello there") as ci:
                        ci.setattr('kk' + repr(ii), default="hello there!", pp="hello somewhere", prod="what?")

                    with rchild_default(name='c' + repr(ii), aa="HELLO THERE") as ci:
                        ci.setattr('ll' + repr(ii), default="HELLO THERE!", pp="HELLO SOMEWHERE", prod="WHAT?")
                        ci.setattr('aa', pp="HELLO SOMEWHERE", prod="WHAT?")

                with rchild_env(name='nn' + repr(ii)) as ci:
                    ci.setattr('oo' + repr(ii), dev1=7, dev2=8, tst=9, pp=18, prod=5)
                    ci.setattr('pp' + repr(ii), g_dev=8, tst=9, pp=19, prod=3)

                with rchild_env(name='c' + repr(ii)) as ci:
                    ci.setattr('qq' + repr(ii), default=7, g_dev=8, tst=9, pp=18, prod=5)
                    ci.setattr('rr' + repr(ii), g_dev=8, tst=9, pp=19, prod=3)

    if heap_check:
        print(hp.heap())

    for ii in range(0, 5):
        for jj in range(0, first_range):
            assert cr.children_init[repr(jj)].bb == 1
        for jj in range(0, second_range):
            assert getattr(cr.children_default[repr(jj)], 'a' + str(jj)) == 2
        for jj in range(0, third_range):
            assert getattr(cr.children_env[repr(jj)], 'bb' + str(jj)) == 3

    return cr


cProfile.run("perf1()", "perf.profile")
