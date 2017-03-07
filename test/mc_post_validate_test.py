# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigApiException
from multiconf.envs import EnvFactory

from .utils.tstclasses import ItemWithAA



ef = EnvFactory()
prod = ef.Env('prod')

ef2_pp_prod = EnvFactory()
pp2 = ef2_pp_prod.Env('pp')
prod2 = ef2_pp_prod.Env('prod')
ef2_pp_prod.EnvGroup('g_prod_like', prod2, pp2)


def test_mc_post_validate_getattr_env():
    class root(ItemWithAA):
        def mc_init(self):
            self.aa = 7

        def mc_post_validate(self):
            assert self.getattr('aa', prod2) == self.getattr('aa', pp2) == 7

    @mc_config(ef2_pp_prod)
    def _(_):
        with root():
            pass

    rt = ef2_pp_prod.config(prod2).root
    assert rt.aa == 7


def test_setattr_not_allowed_in_mc_post_validate():
    class root(ConfigItem):
        def mc_post_validate(self):
            self.setattr('y', default=7, mc_set_unknown=True)

    with raises(ConfigApiException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with root():
                pass

    exp = "Trying to set attribute 'y'. Setting attributes is not allowed after configuration is loaded (in order to enforce derived value validity)."
    assert str(exinfo.value) == exp


def test_item_dot_attr_not_allowed_in_mc_post_validate():
    class root(ItemWithAA):
        def mc_post_validate(self):
            print(self.aa)

    with raises(ConfigApiException) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with root() as rt:
                rt.aa = 1

    exp = "Trying to access attribute 'aa'. "
    exp += "Item.attribute access is not allowed in 'mc_post_validate' as there i no current env, use: item.getattr(attr_name, env)"
    assert str(exinfo.value) == exp


def test_mc_post_validate_exception():
    class item(ConfigItem):
        def mc_post_validate(self):
            raise Exception("Error in item mc_post_validate")

    with raises(Exception) as exinfo:
        @mc_config(ef2_pp_prod)
        def _(_):
            with ConfigItem():
                item()

    assert str(exinfo.value) == "Error in item mc_post_validate"
