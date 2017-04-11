# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, MC_REQUIRED
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA


ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)


def test_getattr_env():
    class root(ItemWithAA):
        def mc_init(self):
            self.setattr('aa', default=7, prod=8)

    @mc_config(ef2_pp_prod)
    def _(_):
        root()

    rt = ef2_pp_prod.config(prod2).root
    assert rt.aa == 8
    assert rt.getattr('aa', pp2) == 7
    assert rt.getattr('aa', prod2) == 8

    rt = ef2_pp_prod.config(pp2).root
    assert rt.aa == 7
    assert rt.getattr('aa', pp2) == 7
    assert rt.getattr('aa', prod2) == 8


def test_getattr_property():
    class root(ConfigItem):
        @property
        def myprop(self):
            return 17

    @mc_config(ef2_pp_prod)
    def _(_):
        root()

    rt = ef2_pp_prod.config(prod2).root
    assert rt.myprop == 17
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 17

    rt = ef2_pp_prod.config(pp2).root
    assert rt.myprop == 17
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 17


def test_getattr_overwritten_property():
    class root(ConfigItem):
        @property
        def myprop(self):
            return 17

    @mc_config(ef2_pp_prod)
    def _(_):
        with root() as rt:
            rt.setattr('myprop', prod=18, mc_overwrite_property=True)

    rt = ef2_pp_prod.config(prod2).root
    assert rt.myprop == 18
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 18

    rt = ef2_pp_prod.config(pp2).root
    assert rt.myprop == 17
    assert rt.getattr('myprop', pp2) == 17
    assert rt.getattr('myprop', prod2) == 18


def test_getattr_overwritten_property_ref_mc_attribute():
    class root(ConfigItem):
        def __init__(self, xx=MC_REQUIRED):
            super(root, self).__init__()
            self.xx = xx

        @property
        def myprop(self):
            return self.xx + 1

    @mc_config(ef2_pp_prod)
    def _(_):
        with root() as rt:
            rt.setattr('xx', pp=15, prod=16)
            rt.setattr('myprop', prod=18, mc_overwrite_property=True)

    rt = ef2_pp_prod.config(prod2).root
    assert rt.myprop == 18
    assert rt.getattr('myprop', pp2) == 16
    assert rt.getattr('myprop', prod2) == 18

    rt = ef2_pp_prod.config(pp2).root
    assert rt.myprop == 16
    assert rt.getattr('myprop', pp2) == 16
    assert rt.getattr('myprop', prod2) == 18


def test_getattr_overwritten_property_error():
    class root(ConfigItem):
        def __init__(self, xx=MC_REQUIRED):
            super(root, self).__init__()
            self.xx = xx

        @property
        def myprop(self):
            raise Exception("Error in myprop")

    @mc_config(ef2_pp_prod, validate_properties=False)
    def _(_):
        with root() as rt:
            rt.setattr('xx', pp=15, prod=16)
            rt.setattr('myprop', prod=18, mc_overwrite_property=True)

    rt = ef2_pp_prod.config(prod2).root
    assert rt.myprop == 18
    with raises(Exception):
        _ = rt.getattr('myprop', pp2)

    assert rt.getattr('myprop', prod2) == 18

    rt = ef2_pp_prod.config(pp2).root

    with raises(Exception):
        _ = rt.myprop

    with raises(Exception):
        _ = rt.getattr('myprop', pp2)

    assert rt.getattr('myprop', prod2) == 18
