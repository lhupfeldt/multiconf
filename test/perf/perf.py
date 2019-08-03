#!/usr/bin/python3

# Copyright (c) 2012 - 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
import cProfile
import timeit

import click

import os.path
from os.path import join as jp
here = os.path.dirname(__file__)
sys.path.insert(0, jp(here, '..', '..'))

from multiconf import mc_config, ConfigItem, RepeatableConfigItem
from multiconf.decorators import nested_repeatables, named_as, required
from multiconf.envs import EnvFactory


ef = None
prod = None
conf = None


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
        super().__init__(mc_key=mc_key)
        self.name = mc_key
        self.aa = aa
        self.bb = bb
        self.xx = xx
        self.yy = yy


@named_as('children_mc_init')
class rchild_mc_init(RepeatableConfigItem):
    def __init__(self, mc_key, xx):
        super().__init__(mc_key=mc_key)
        self.name = mc_key
        self.xx = xx

    def mc_init(self):
        super().mc_init()
        self.setattr('xx', default=17, mc_force=True)
        self.setattr('yy', default=18, mc_set_unknown=True, mc_force=True)
        self.setattr('zz', default=19, mc_set_unknown=True, mc_force=True)


@named_as('children_default')
class rchild_default(RepeatableConfigItem):
    def __init__(self, mc_key, aa):
        super().__init__(mc_key=mc_key)
        self.name = mc_key
        self.aa = aa


@named_as('children_env')
@nested_repeatables('children_init', 'children_default', 'children_env', 'children_mc_init')
class rchild_env(RepeatableConfigItem):
    def __init__(self, name):
        super().__init__(mc_key=name)
        self.name = name


first_range = 100
second_range = 100
third_range = 100


def config(validate_properties=True, lazy_load=False):
    global hp
    global conf

    @mc_config(ef)
    def conf_func(_):
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

    conf_func.load(validate_properties=validate_properties, lazy_load=lazy_load)
    conf = conf_func


def use():
    global conf

    cr = conf(prod).root
    for ii in range(0, 5):
        for jj in range(0, first_range):
            assert cr.children_init[repr(jj)].bb == 1
        for jj in range(0, second_range):
            assert getattr(cr.children_default[repr(jj)], 'a' + str(jj)) == 2
        for jj in range(0, third_range):
            assert getattr(cr.children_env[repr(jj)], 'bb' + str(jj)) == 3


@click.command()
@click.option("--time/--no-time", default=True)
@click.option("--profile/--no-profile", default=False)
def cli(time, profile):
    if time:
        def _test(name, ff, test, setup, repeat, number):
            times = sorted(timeit.repeat(test, setup=setup, repeat=repeat, number=number))
            times = ["{:.4f}".format(tt) for tt in times]
            print(name, times)
            print(name, times, file=ff)

        tfile = jp(here, "times.txt")
        if os.path.exists(tfile):
            with open(tfile) as ff:
                print('previous:')
                print(ff.read())
            print('new:')

        with open(tfile, 'w') as ff:
            _test("envs", ff, "envs_setup()", setup="from __main__ import envs_setup", repeat=10, number=20000)
            _test("load - lazy", ff, "config(validate_properties=False, lazy_load=True); from __main__ import conf; conf(prod)",
                  setup="from __main__ import config, conf, prod", repeat=10, number=10)
            _test("use_validate_lazy", ff, "use()", setup="from __main__ import use", repeat=1, number=1)
            _test("load - no @props", ff, "config(validate_properties=False)", setup="from __main__ import config", repeat=10, number=10)
            _test("load - @props", ff, "config(validate_properties=True)", setup="from __main__ import config", repeat=10, number=10)
            _test("use", ff, "use()", setup="from __main__ import use", repeat=10, number=300)

    if profile:
        cProfile.run("envs_setup()", jp(here, "envs_setup.profile"))
        cProfile.run("config()", jp(here, "config.profile"))
        cProfile.run("use()", jp(here, "use.profile"))


if __name__ == "__main__":
    cli()
