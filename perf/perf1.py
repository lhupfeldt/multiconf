#!/usr/bin/python

# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.
import cProfile

import sys
import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.append(jp(here, '../..'))

from multiconf import ConfigRoot, ConfigItem
from multiconf.decorators import nested_repeatables, named_as, repeat, required
from multiconf.envs import EnvFactory

ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')

pp = ef.Env('pp')
prod = ef.Env('prod')

g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)

valid_envs = [g_dev, tst, g_prod_like]

@nested_repeatables('children_init, children_default, children_env, children_mc_init')
class root(ConfigRoot):
    pass


@named_as('children_init')
@repeat()
class rchild_init(ConfigItem):
    pass


@named_as('children_mc_init')
@repeat()
class rchild_mc_init(ConfigItem):
    def mc_init(self):
        super(rchild_mc_init, self).mc_init()
        self.override('xx', 17)
        self.override('yy', 17)


@named_as('children_default')
@repeat()
class rchild_default(ConfigItem):
    pass


@named_as('children_env')
@nested_repeatables('children_init, children_default, children_env, children_mc_init')
@repeat()
class rchild_env(ConfigItem):
    pass


def perf1():
    first_range = 1000
    second_range = 1000
    third_range = 1000

    with root(prod, ef) as cr:
        for ii in xrange(0, first_range):
            rchild_init(name=repr(ii), aa=1, bb=1)

        for ii in xrange(0, second_range):
            with rchild_default(name=repr(ii), aa=4) as ci:
                ci.setattr('bb', default=2)

        for ii in xrange(0, third_range):
            with rchild_env(name=repr(ii)) as ci:
                ci.setattr('aa', dev1=7, dev2=8, tst=9, pp=18, prod=5)
                ci.setattr('bb', g_dev=8, tst=9, pp=19, prod=3)

                with rchild_env(name='a' + repr(ii)) as ci:
                    ci.setattr('aa', dev1=7, dev2=8, tst=9, pp=18, prod=5)
                    ci.setattr('bb', g_dev=8, tst=9, pp=19, prod=3)

                    for ii in xrange(0, 10):
                        with rchild_default(name='a' + repr(ii), aa=4) as ci:
                            ci.setattr('bb', default=2, pp=3, prod=4)

                        with rchild_mc_init(name='b' + repr(ii), xx=7) as ci:
                            ci.setattr('xx', default=2, pp=3, prod=4)
                            ci.setattr('yy', default=2, pp=3, prod=4)

                    with rchild_default(name='b' + repr(ii), aa="hello there") as ci:
                        ci.setattr('bb', default="hello there!", pp="hello somewhere", prod="what?")

                    with rchild_default(name='c' + repr(ii), aa="HELLO THERE") as ci:
                        ci.setattr('bb', default="HELLO THERE!", pp="HELLO SOMEWHERE", prod="WHAT?")
                        ci.setattr('aa', pp="HELLO SOMEWHERE", prod="WHAT?")

                with rchild_env(name='b' + repr(ii)) as ci:
                    ci.setattr('aa', dev1=7, dev2=8, tst=9, pp=18, prod=5)
                    ci.setattr('bb', g_dev=8, tst=9, pp=19, prod=3)

                with rchild_env(name='c' + repr(ii)) as ci:
                    ci.setattr('aa', default=7, g_dev=8, tst=9, pp=18, prod=5)
                    ci.setattr('bb', g_dev=8, tst=9, pp=19, prod=3)
    
    for ii in range(0, 5):
        for ii in xrange(0, first_range):
            assert cr.children_init[repr(ii)].bb == 1
        for ii in xrange(0, second_range):
            assert cr.children_default[repr(ii)].bb == 2
        for ii in xrange(0, third_range):
            assert cr.children_env[repr(ii)].bb == 3


cProfile.run("perf1()", "perf1.profile")

