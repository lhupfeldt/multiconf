# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import xfail

from multiconf import mc_config, ConfigItem, MC_REQUIRED

from multiconf.envs import EnvFactory

ef = EnvFactory()

dev1 = ef.Env('dev1')
dev2 = ef.Env('dev2')
g_dev = ef.EnvGroup('g_dev', dev1, dev2)

tst = ef.Env('tst')
ef.EnvGroup('g_dev_tst', g_dev, tst)

pp = ef.Env('pp')
prod = ef.Env('prod')
ef.EnvGroup('g_prod', pp, prod)


class item1(ConfigItem):
    def __init__(self):
        super(item1, self).__init__()
        self.aa = MC_REQUIRED

    def mc_init(self):
        print("MC_INIT 1")
        self.setattr('aa', g_dev=2, dev1=7)


class item2(ConfigItem):
    def __init__(self):
        super(item2, self).__init__()
        self.aa = MC_REQUIRED

    def mc_init(self):
        print("MC_INIT 2")
        self.setattr('aa', g_dev_tst=2)


def test_direct_env_in_mc_init_overrides_default_and_group_in_with():
    @mc_config(ef)
    def _(_):
        with item1() as it:
            it.aa = 13
    it = ef.config(dev1).item1
    assert it.aa == 7

    @mc_config(ef)
    def _(_):
        with item1() as it:
            it.setattr('aa', default=13)
    it = ef.config(dev1).item1
    assert it.aa == 7

    @mc_config(ef)
    def _(_):
        with item1() as it:
            it.setattr('aa', default=1, g_dev=13)
    it = ef.config(dev1).item1
    assert it.aa == 7

    @mc_config(ef)
    def _(_):
        with item1() as it:
            it.setattr('aa', default=1, g_dev_tst=13)
    it = ef.config(dev1).item1
    assert it.aa == 7


def test_direct_env_in_with_overrides_mc_init():
    @mc_config(ef)
    def _(_):
        with item1() as it:
            it.setattr('aa', dev1=1, tst=111, g_dev=7, g_prod=17)
    it = ef.config(dev1).item1
    assert it.aa == 1


def test_more_specific_group_in_with_overrides_mc_init():
    @mc_config(ef)
    def _(_):
        with item2() as it:
            it.setattr('aa', g_dev=1, tst=111, g_prod=17)
    it = ef.config(dev1).item2
    assert it.aa == 1
