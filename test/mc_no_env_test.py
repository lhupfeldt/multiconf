# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import (
    mc_config, ConfigItem, RepeatableConfigItem, ConfigException, ConfigApiException, ConfigExcludedAttributeError, McInvalidValue, MC_REQUIRED)
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory, MC_NO_ENV

from .utils.tstclasses import ItemWithAA, RepeatableItemWithAA
from .utils.utils import local_func


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')
g_prod_like = ef.EnvGroup('g_prod_like', prod, pp)


@nested_repeatables('children')
class nc_aa_root(ItemWithAA):
    pass


@named_as('children')
class rchild(RepeatableItemWithAA):
    pass


def test_repeatable_items_mc_select_envs_excluded_no_env():
    @mc_config(ef, load_now=True)
    def config(root):
        with nc_aa_root(1) as cr:
            with rchild("first") as ci:
                ci.mc_select_envs(exclude=[prod])
                ci.setattr('aa', pp=1)

            with rchild("second") as ci:
                ci.mc_select_envs(exclude=[pp])
                ci.setattr('aa', prod=3)

            with rchild("third") as ci:
                ci.setattr('aa', prod=4, pp=3)

            with rchild("fourth") as ci:
                ci.setattr('aa', prod=5, pp=4)

            with rchild("fifth") as ci:
                ci.mc_select_envs(exclude=[prod])
                ci.setattr('aa', pp=5)

    cr = config(MC_NO_ENV).nc_aa_root

    assert len(cr.children) == 5

    with raises(ConfigApiException) as ex:
        for ci in cr.children.values():
            assert ci.aa

    exp_ex = "Trying to access attribute 'aa'. " \
             "Item.attribute access is not allowed when config is instantiated with 'MC_NO_ENV'. " \
             "Use: item.attr_env_items('aa') or item.getattr('aa', <env>)"
    assert str(ex.value) == exp_ex

    with raises(ConfigExcludedAttributeError) as exinfo:
        cr.children['first'].getattr('aa', prod)
    exp_ex = "Accessing attribute 'aa' for Env('prod') on an excluded config item: Excluded: <class 'test.mc_no_env_test.rchild'>"
    assert exp_ex in str(exinfo.value)
    assert cr.children['first'].getattr('aa', pp) == 1

    exp_envs = [pp, prod]
    exp_values = [1, McInvalidValue.MC_NO_VALUE]
    for index, (env, val) in enumerate(cr.children['first'].attr_env_items('aa')):
        assert env == exp_envs[index]
        assert val == exp_values[index]

    assert cr.children['second'].getattr('aa', prod) == 3
    with raises(ConfigExcludedAttributeError) as exinfo:
        cr.children['second'].getattr('aa', pp)

    assert cr.children['third'].getattr('aa', prod) == 4
    assert cr.children['third'].getattr('aa', pp) == 3

    assert cr.children['fourth'].getattr('aa', prod) == 5
    assert cr.children['fourth'].getattr('aa', pp) == 4

    with raises(ConfigExcludedAttributeError) as exinfo:
        cr.children['fifth'].getattr('aa', prod)
    exp_ex = "Accessing attribute 'aa' for Env('prod') on an excluded config item: Excluded: <class 'test.mc_no_env_test.rchild'>"
    assert exp_ex in str(exinfo.value)
    assert cr.children['fifth'].getattr('aa', pp) == 5


def test_repeatable_items_skipped_in_envs():
    @mc_config(ef, load_now=True)
    def config(root):
        with nc_aa_root(1) as cr:
            cr.setattr('num_children', pp=2, prod=4, mc_set_unknown=True)
            for ii in range(0, cr.num_children):
                rchild("num" + str(ii), aa=27)

    cr = config(MC_NO_ENV).nc_aa_root
    assert len(cr.children) == 4

    cr = config(pp).nc_aa_root
    assert len(cr.children) == 2


def test_repeatable_items_bool():
    @named_as('Xs')
    class X(RepeatableConfigItem):
        pass

    @named_as('Ys')
    class Y(RepeatableConfigItem):
        pass

    @nested_repeatables('Xs', 'Ys', 'Zs')
    class HasRepeatables(ConfigItem):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with HasRepeatables() as y:
            with X(mc_key='aa') as xx:
                xx.mc_select_envs(exclude=[g_prod_like])
            with X(mc_key='bb') as xx:
                xx.mc_select_envs(exclude=[pp])
            with X(mc_key='cc') as xx:
                xx.mc_select_envs(exclude=[g_prod_like])

            Y(mc_key='aa')
            Y(mc_key='bb')
            Y(mc_key='cc')

    rep = config(MC_NO_ENV).HasRepeatables
    assert rep.Xs
    assert rep.Ys
    assert not rep.Zs


def test_lazy_load_no_env():
    @mc_config(ef)
    def config(_):
        pass

    with raises(ConfigException) as exinfo:
        config.load(lazy_load=True)(MC_NO_ENV)

    exp_ex = "Env('MC_NO_ENV') cannot be used with 'lazy_load'."
    assert exp_ex in str(exinfo.value)


def test_mc_env_loop():
    class item(ConfigItem):
        def __init__(self, aa):
            super().__init__()
            self.aa = aa
            self.aa_alternate = MC_REQUIRED

        @property
        def aa_special(self):
            return self.aa_alternate + self.aa

    @mc_config(ef, load_now=True)
    def config(root):
        with item(aa=1) as it:
            it.setattr('aa_alternate', default=1, prod=7)

    cr = config(MC_NO_ENV)

    exp_envs = [pp, prod]
    exp_values = [2, 8]
    for index, env in enumerate(cr.item.env_loop()):
        assert env is exp_envs[index]
        assert cr.item.aa == 1
        assert cr.item.aa_special is exp_values[index]
