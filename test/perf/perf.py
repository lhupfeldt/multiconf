#!/usr/bin/python

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import cProfile
import timeit

heap_check = sys.version_info.major < 3 and len(sys.argv) > 1 and sys.argv[1] == 'mem'
if heap_check:
    from guppy import hpy
    hp = hpy()

import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.insert(0, jp(here, '..', '..'))

from multiconf import mc_config, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory


ef = None
prod = None

def envs_setup():
    global ef
    global prod

    ef = EnvFactory()

    dev1 = ef.Env('dev1')
    dev2 = ef.Env('dev2')
    g_dev = ef.EnvGroup('g_dev', dev1, dev2)

    tst = ef.Env('tst')

    pp = ef.Env('pp')
    prod = ef.Env('prod')

    g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children_init', 'children_default', 'children_env', 'children_mc_init')
class root(ConfigItem):
    pass


@named_as('children_init')
class rchild_init(RepeatableConfigItem):
    def __init__(self, mc_key, aa, bb, xx, yy):
        super(rchild_init, self).__init__(mc_key=mc_key)
        self.name = mc_key
        self.aa = aa
        self.bb = bb
        self.xx = xx
        self.yy = yy


@named_as('children_mc_init')
class rchild_mc_init(RepeatableConfigItem):
    def __init__(self, mc_key, xx):
        super(rchild_mc_init, self).__init__(mc_key=mc_key)
        self.name = mc_key
        self.xx = xx

    def mc_init(self):
        super(rchild_mc_init, self).mc_init()
        self.setattr('xx', default=17, mc_force=True)
        self.setattr('yy', default=18, mc_set_unknown=True, mc_force=True)
        self.setattr('zz', default=19, mc_set_unknown=True, mc_force=True)


@named_as('children_default')
class rchild_default(RepeatableConfigItem):
    def __init__(self, mc_key, aa):
        super(rchild_default, self).__init__(mc_key=mc_key)
        self.name = mc_key
        self.aa = aa


@named_as('children_env')
@nested_repeatables('children_init', 'children_default', 'children_env', 'children_mc_init')
class rchild_env(RepeatableConfigItem):
    def __init__(self, name):
        super(rchild_env, self).__init__(mc_key=name)
        self.name = name


first_range = 2000
second_range = 2000
third_range = 2000


def perf_config():
    @mc_config(ef)
    def _(_):
        with root() as cr:
            for ii in range(0, first_range):
                rchild_init(repr(ii), aa=1, bb=1, xx="hello", yy="hi")

            for ii in range(0, second_range):
                with rchild_default(repr(ii), aa=4) as ci:
                    ci.setattr('a' + repr(ii), default=2, mc_set_unknown=True)

            for ii in range(0, third_range):
                with rchild_env(repr(ii)) as ci:
                    ci.setattr('aa' + repr(ii), dev1=7, dev2=8, tst=9, pp=18, prod=5, mc_set_unknown=True)
                    ci.setattr('bb' + repr(ii), g_dev=8, tst=9, pp=19, prod=3, mc_set_unknown=True)
                    ci.setattr('x' + repr(ii), g_dev=8, tst=9, pp=19, prod=3, mc_set_unknown=True)
                    ci.setattr('y' + repr(ii), g_dev=8, tst=9, pp=19, prod=3, mc_set_unknown=True)
                    ci.setattr('z' + repr(ii), g_dev=8, tst=9, pp=19, prod=3, mc_set_unknown=True)

                    with rchild_env('a' + repr(ii)) as ci:
                        ci.setattr('cc' + repr(ii), dev1=7, dev2=8, tst=9, pp=18, prod=5, mc_set_unknown=True)
                        ci.setattr('dd' + repr(ii), g_dev=8, tst=9, pp=19, prod=3, mc_set_unknown=True)

                        for jj in range(0, 10):
                            with rchild_default('ee' + repr(ii) + '_' + repr(jj), aa=4) as ci:
                                ci.setattr('ff' + repr(ii) + '_' + repr(jj), default=2, pp=3, prod=4, mc_set_unknown=True)

                            with rchild_mc_init('gg' + repr(ii) + '_' + repr(jj), xx=7) as ci:
                                ci.setattr('hh' + repr(ii) + '_' + repr(jj), default=2, pp=3, prod=4, mc_set_unknown=True)
                                ci.setattr('ii' + repr(ii) + '_' + repr(jj), default=2, pp=3, prod=4, mc_set_unknown=True)

                        with rchild_default('jj' + repr(ii), aa="hello there") as ci:
                            ci.setattr('kk' + repr(ii), default="hello there!", pp="hello somewhere", prod="what?", mc_set_unknown=True)

                        with rchild_default('c' + repr(ii), aa="HELLO THERE") as ci:
                            ci.setattr('ll' + repr(ii), default="HELLO THERE!", pp="HELLO SOMEWHERE", prod="WHAT?", mc_set_unknown=True)
                            ci.setattr('aa', pp="HELLO SOMEWHERE", prod="WHAT?")

                    with rchild_env('nn' + repr(ii)) as ci:
                        ci.setattr('oo' + repr(ii), dev1=7, dev2=8, tst=9, pp=18, prod=5, mc_set_unknown=True)
                        ci.setattr('pp' + repr(ii), g_dev=8, tst=9, pp=19, prod=3, mc_set_unknown=True)

                    with rchild_env('c' + repr(ii)) as ci:
                        ci.setattr('qq' + repr(ii), default=7, g_dev=8, tst=9, pp=18, prod=5, mc_set_unknown=True)
                        ci.setattr('rr' + repr(ii), g_dev=8, tst=9, pp=19, prod=3, mc_set_unknown=True)

    if heap_check:
        print(hp.heap())


def perf_config_use():
    cr = ef.config(prod).root
    for ii in range(0, 5):
        for jj in range(0, first_range):
            assert cr.children_init[repr(jj)].bb == 1
        for jj in range(0, second_range):
            assert getattr(cr.children_default[repr(jj)], 'a' + str(jj)) == 2
        for jj in range(0, third_range):
            assert getattr(cr.children_env[repr(jj)], 'bb' + str(jj)) == 3



cProfile.run("envs_setup()", jp(here, "envs_setup.profile"))
cProfile.run("perf_config()", jp(here, "per_config.profile"))
cProfile.run("perf_config_use()", jp(here, "perf_config_use.profile"))
