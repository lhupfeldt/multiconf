# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, MC_REQUIRED

from multiconf.envs import EnvFactory

from utils.tstclasses import ItemWithAA, ItemWithAABB

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
        super().__init__()
        self.aa = MC_REQUIRED

    def mc_init(self):
        print("MC_INIT 1")
        self.setattr('aa', g_dev=2, dev1=7)


class item2(ConfigItem):
    def __init__(self):
        super().__init__()
        self.aa = MC_REQUIRED

    def mc_init(self):
        print("MC_INIT 2")
        self.setattr('aa', g_dev_tst=2)


def test_direct_env_in_mc_init_overrides_default_and_group_in_with():
    @mc_config(ef, load_now=True)
    def config(_):
        with item1() as it:
            it.aa = 13
    it = config(dev1).item1
    assert it.aa == 7

    @mc_config(ef, load_now=True)
    def config(_):
        with item1() as it:
            it.setattr('aa', default=13)
    it = config(dev1).item1
    assert it.aa == 7

    @mc_config(ef, load_now=True)
    def config(_):
        with item1() as it:
            it.setattr('aa', default=1, g_dev=13)
    it = config(dev1).item1
    assert it.aa == 7

    @mc_config(ef, load_now=True)
    def config(_):
        with item1() as it:
            it.setattr('aa', default=1, g_dev_tst=13)
    it = config(dev1).item1
    assert it.aa == 7


def test_direct_env_in_with_overrides_mc_init():
    @mc_config(ef, load_now=True)
    def config(_):
        with item1() as it:
            it.setattr('aa', dev1=1, tst=111, g_dev=7, g_prod=17)
    it = config(dev1).item1
    assert it.aa == 1


def test_more_specific_group_in_with_overrides_mc_init():
    @mc_config(ef, load_now=True)
    def config(_):
        with item2() as it:
            it.setattr('aa', g_dev=1, tst=111, g_prod=17)
    it = config(dev1).item2
    assert it.aa == 1


def test_children_in_mc_init_frozen():
    class X1(ItemWithAA):
        def __init__(self, aa):
            super().__init__(aa=aa)
            self.bb = MC_REQUIRED

        def mc_init(self):
            print("X1.mc_init")
            super().mc_init()
            self.aa = 1
            self.bb = 30

    class X2(ItemWithAA):
        def mc_init(self):
            print("X2.mc_init")
            super().mc_init()
            self.aa = 1
            X1(aa=1)

    @mc_config(ef, load_now=True)
    def config0(_):
        with ConfigItem():
            X2(17)
        print('after')

    cr = config0(prod).ConfigItem.X2
    assert cr.aa == 17
    assert cr.X1.aa == 1
    assert cr.X1.bb == 30


def test_children_in_mc_init_only_frozen_once():
    class X1(ItemWithAABB):
        def __init__(self, aa, bb=None):
            super().__init__(aa=aa, bb=bb)
            self.cc = MC_REQUIRED

        def mc_init(self):
            print("X1.mc_init")
            super().mc_init()
            self.aa = 1
            self.bb = 1
            # Access self.aa here, it should be settable again during next env initialization
            self.cc = self.aa + 1

    class X2(ItemWithAABB):
        def mc_init(self):
            print("X2.mc_init")
            super().mc_init()
            self.aa = 1
            self.bb = 1
            X1(aa=1, bb=1)

    @mc_config(ef, load_now=True)
    def config0(_):
        X2(17)

    cr = config0(prod).X2
    assert cr.aa == 17
    assert cr.bb == None
    assert cr.X1.aa == 1
    assert cr.X1.bb == 1
    assert cr.X1.cc == 2
